from utils import positive
from typing import Self


class Vault:
    def __init__(self, money: float, withdrawal: float):
        if not positive(money):
            raise ValueError
        self.money = money
        self.withdrawal = withdrawal
        self.result: float | None = None
        self.stored = 0.0

    def withdraw(self):
        if self.withdrawal < 0.0:
            raise ValueError
        amount = min(self.withdrawal, self.money)
        self.add(-amount)
        return amount

    def win(self, amount: float | None):
        if amount:
            self.add(amount)
        self.result = amount

    def add(self, amount):
        self.money += amount

    def store(self, amount):
        amount = min(amount, self.money)
        self.stored += amount
        self.money -= amount

    def snapshot(self):
        snapshot = Vault(self.money, self.withdrawal)
        snapshot.restore(self)
        return snapshot

    def restore(self, snapshot: Self):
        self.money = snapshot.money
        self.result = snapshot.result
        self.stored = snapshot.stored

    @property
    def total(self):
        return self.money + self.stored
