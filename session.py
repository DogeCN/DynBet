from vault import Vault
from game import Game
from strategy import Strategy
from data import Data


class Session:
    def __init__(self, game: Game, vault: Vault):
        self.data = Data(vault)
        self.game = game
        self.vault = vault

    def run(self, strategy: Strategy):
        bet = strategy.bet(self.vault.snapshot(), self.data)
        result = self.game.once(bet.withdraw())
        bet.win(result)
        self.data.append(bet)
        self.vault.restore(bet)
        return bet

    def rollback(self, turn: int):
        if not self.data.turn >= turn >= 0:
            raise ValueError
        self.vault.restore(self.data.rollback(turn).vault)
