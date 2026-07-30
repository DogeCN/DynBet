from game import Game
from utils import positive, same
from functools import cached_property
import random


class Dice(Game):
    def __init__(self, dice: list[int], amount: int, rate: float):
        self.dice = dice
        if not positive(self.length, amount, rate):
            raise ValueError
        self.amount = amount
        self.rate = rate

    def once(self, bet: float) -> float | None:
        if self.random():
            return bet * self.rate

    def random(self) -> bool:
        result = [self.roll() for _ in range(self.amount)]
        if same(result):
            return False
        total = sum(result)
        return total >= self.mean

    def roll(self):
        return random.choice(self.dice)

    @property
    def length(self):
        return len(self.dice)

    @cached_property
    def mean(self):
        return (sum(self.dice) * self.amount + self.length - 1) // self.length
