from typing import Any, Callable

from pyacorn.chains.base import Body


class Lambda[I, O](Body[I, O]):
    def __init__(self, func: Callable[[I], O]):
        super().__init__()
        self.func = func

    def operate(self, data: I):
        return self.func(data)

class Printer[T](Lambda[T, None]):
    def __init__(self, transform: Callable[[T], Any] = lambda x: x):
        super().__init__(func=lambda x: print(transform(x)))