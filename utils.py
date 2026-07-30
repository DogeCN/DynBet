from typing import Iterable


class LCList[T]:
    def __init__(self, sequence: Iterable[T]):
        self.iterator = iter(sequence)
        self.cache = []

    def __getitem__(self, index: int):
        i = len(self.cache) - 1
        while i < index:
            try:
                self.cache.append(next(self.iterator))
                i += 1
            except StopIteration:
                break
        return self.cache[min(index, i)]


def same(source):
    return all(x == source[0] for x in source[1:])


def positive(*nums: float) -> bool:
    return all(x > 0 for x in nums)
