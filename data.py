from typing import Self
from vault import Vault


class Node:
    def __init__(self, prev: Self, bet: Vault):
        self.vault = bet
        sign = 2 * self.won - 1
        self.win = prev.win + self.won
        self.streak = prev.streak + sign if prev.streak * sign > 0 else sign
        self.peak = max(prev.peak, self)
        self.lowest = min(prev.lowest, self)

    @classmethod
    def origin(cls, vault: Vault) -> Self:
        instance = cls.__new__(cls)
        instance.win = 0
        instance.streak = 0
        instance.vault = vault.snapshot()
        instance.peak = instance
        instance.lowest = instance
        return instance

    @property
    def won(self) -> bool:
        return bool(self.vault.result)

    def __gt__(self, other: Self):
        return self.vault.money > other.vault.money

    def __lt__(self, other: Self):
        return self.vault.money < other.vault.money


class Data:
    def __init__(self, vault: Vault):
        self.nodes = [Node.origin(vault)]

    def append(self, bet: Vault):
        self.nodes.append(Node(self.latest, bet))

    def rollback(self, turn: int) -> Node:
        del self.nodes[turn + 1 :]
        return self.latest

    @property
    def turn(self) -> int:
        return len(self.nodes) - 1

    @property
    def streak(self) -> int:
        return self.nodes[-1].streak

    @property
    def win(self) -> int:
        return self.nodes[-1].win

    @property
    def loss(self) -> int:
        return self.turn - self.win

    @property
    def peak(self) -> Node:
        return self.latest.peak

    @property
    def lowest(self) -> Node:
        return self.latest.lowest

    @property
    def origin(self) -> Node:
        return self.nodes[0]

    @property
    def latest(self) -> Node:
        return self.nodes[-1]
