from typing import Callable

from pyacorn.chains.base import Body


class Lambda[I, O](Body[I, O]):
    def __init__(self, func: Callable[[I], O]):
        super().__init__()
        self.func = func

    def operate(self, data: I):
        return self.func(data)