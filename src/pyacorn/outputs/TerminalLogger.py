
from typing import Any, Callable

from pyacorn.chains import Lambda


class Printer[T](Lambda[T, None]):
    def __init__(self, transform: Callable[[T], Any] = lambda x: x):
        super().__init__(func=lambda x: print(transform(x)))