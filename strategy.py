from vault import Vault
from data import Data, Node
from utils import LCList, positive
from weakref import WeakKeyDictionary as WKD
from typing import Self
import random
import copy


class Strategy:
    def __init__(self):
        self.pipe: list[Strategy] = []

    def apply(self, strategy: Self):
        self.pipe.append(strategy)
        return self

    def bet(self, vault: Vault, data: Data) -> Vault:
        for s in self.pipe:
            vault = s.bet(vault, data)
        return vault

    def copy(self) -> Self:
        return copy.copy(self)


class Flat(Strategy):
    def __init__(self, base: float):
        super().__init__()
        if not positive(base):
            raise ValueError
        self.base = base

    def bet(self, vault: Vault, _: Data) -> Vault:
        vault.withdrawal = self.base
        return vault


class Allin(Strategy):
    def bet(self, vault: Vault, _: Data) -> Vault:
        vault.withdrawal = vault.money
        return vault


class Random(Strategy):
    def bet(self, vault: Vault, _: Data) -> Vault:
        vault.withdrawal = random.uniform(0, vault.money)
        return vault


class Ratio(Strategy):
    def __init__(self, ratio: float):
        super().__init__()
        self.ratio = ratio

    def bet(self, vault: Vault, _: Data) -> Vault:
        vault.withdrawal = vault.withdrawal * self.ratio
        return vault


class Progressive[T](Strategy):
    def __init__(self, origin: T, reverse: bool = False):
        super().__init__()
        self.origin = origin
        self.reverse = reverse
        self.cache: WKD[Data, WKD[Node, T]] = WKD()

    def transition(self, state: T, node: Node) -> T:
        raise NotImplementedError

    def get(self, vault: Vault, data: Data, state: T) -> Vault:
        raise NotImplementedError

    def bet(self, vault: Vault, data: Data) -> Vault:
        try:
            cache = self.cache[data]
        except KeyError:
            cache = WKD({data.origin: self.origin})
            self.cache[data] = cache
        cursor = len(cache)
        while cursor <= data.turn:
            current = data.nodes[cursor]
            prev = data.nodes[cursor - 1]
            cache[current] = self.transition(cache[prev], current)
            cursor += 1
        return self.get(vault, data, cache[data.latest])


class Martingale(Progressive[int]):
    def __init__(self, reverse: bool = False):
        super().__init__(0, reverse)

    def transition(self, state: int, node: Node) -> int:
        return 0 if self.reverse ^ node.won else state + 1

    def get(self, vault: Vault, data: Data, state: int) -> Vault:
        vault.withdrawal *= 2**state
        return vault


class DAlembert(Progressive[float]):
    def __init__(self, unit: float = 1.0, reverse: bool = False):
        super().__init__(unit, reverse)

    def transition(self, state: float, node: Node) -> float:
        return max(self.origin, state + (node.won == self.reverse) * 2 - 1)

    def get(self, vault: Vault, data: Data, state: float) -> Vault:
        vault.withdrawal *= state
        return vault


class Fibonacci(Progressive[int]):
    def fibonacci():
        a = b = 1
        while True:
            yield a
            a, b = b, a + b

    def __init__(self, reverse: bool = False):
        super().__init__(0, reverse)
        self.seq = LCList(Fibonacci.fibonacci())

    def transition(self, state: int, node: Node) -> int:
        return max(0, state - 2) if self.reverse == node.won else state + 1

    def get(self, vault: Vault, data: Data, state: int) -> Vault:
        vault.withdrawal *= self.seq[state]
        return vault


class Stepping(Progressive[int]):
    def __init__(self, multipliers: list[int], reverse: bool = False):
        super().__init__(0, reverse)
        self.multipliers = multipliers

    def transition(self, state: int, node: Node) -> int:
        reset = self.reverse == node.won
        return 0 if reset else (state + 1) % len(self.multipliers)

    def get(self, vault: Vault, data: Data, state: int) -> Vault:
        vault.withdrawal *= self.multipliers[state]
        return vault


class Labouchere(Progressive[list[Strategy]]):
    def __init__(self, strategy: Strategy, reverse: bool = False):
        super().__init__([], reverse)
        self.strategy = strategy

    def transition(self, state: list[Strategy], node: Node) -> list[Strategy]:
        if state:
            state = state[:]
            if self.reverse != node.won:
                state.pop()
                if len(state) >= 2:
                    state.pop(0)
            else:
                state.append(self.sum(state))
        return state

    def apply(self, strategy: Self):
        self.origin.append(strategy)
        return self

    def sum(self, state: list[Strategy]) -> Strategy:
        target = {state[0], state[-1]}
        sum = Sum()
        for s in target:
            sum = sum.apply(s)
        return sum

    def get(self, vault: Vault, data: Data, state: list[Strategy]) -> Vault:
        strategy = self.sum(state) if state else self.strategy
        return strategy.bet(vault, data)


class Fork(Strategy):
    def __init__(self, strategy: Strategy):
        super().__init__()
        self.strategy = strategy

    def bet(self, vault: Vault, data: Data) -> Vault:
        if self.fork(vault, data):
            return self.strategy.bet(vault, data)
        return super().bet(vault, data)

    def fork(self, vault: Vault, data: Data) -> bool:
        raise NotImplementedError


class Peak(Fork):
    def fork(self, vault: Vault, data: Data) -> bool:
        return vault.money >= data.peak.vault.money


class Lowest(Fork):
    def fork(self, vault: Vault, data: Data) -> bool:
        return vault.money <= data.lowest.vault.money


class Lock(Fork):
    def fork(self, vault: Vault, data: Data) -> bool:
        mock = vault.snapshot()
        result = self.strategy.bet(mock, data)
        vault.store(result.withdrawal)
        return False


class Aggregator(Strategy):
    def bet(self, vault: Vault, data: Data) -> Vault:
        if self.pipe:
            candidates = [s.bet(vault.snapshot(), data) for s in self.pipe]
            return self.fusion(vault, data, candidates)
        return vault

    def fusion(self, vault: Vault, data: Data, candidates: list[Vault]) -> Vault:
        raise NotImplementedError


class Max(Aggregator):
    def fusion(self, vault: Vault, data: Data, candidates: list[Vault]) -> Vault:
        best = candidates[0]
        for v in candidates[1:]:
            if v.withdrawal > best.withdrawal:
                best = v
        return best


class Min(Aggregator):
    def fusion(self, vault: Vault, data: Data, candidates: list[Vault]) -> Vault:
        best = candidates[0]
        for v in candidates[1:]:
            if v.withdrawal < best.withdrawal:
                best = v
        return best


class Sum(Aggregator):
    def fusion(self, vault: Vault, data: Data, candidates: list[Vault]) -> Vault:
        vault.withdrawal = sum(map(lambda v: v.withdrawal, candidates))
        return vault
