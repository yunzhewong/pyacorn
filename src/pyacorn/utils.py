from typing import Callable, TypeVar

I = TypeVar("I")

class CallbackMap(dict[int, Callable[[I], None]]):
    def __init__(self, iterable):
        super().__init__(iterable)
        self.key_counter = 0

    def add(self, callback: Callable[[I], None]) -> int:
        callback_key = self.key_counter
        self[callback_key] = callback
        self.key_counter += 1
        return callback_key

    def remove(self, key):
        del self[key]

    def execute(self, data: I):
        for callback in self.values():
            callback(data)
