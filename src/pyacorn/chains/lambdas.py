from collections.abc import Callable

from .base import OperationBody


class Lambda[I, O](OperationBody[I, O]):
    def __init__(self, func: Callable[[I], O]):
        super().__init__()
        self.func = func

    def operate(self, data: I):
        return self.func(data)
