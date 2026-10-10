from collections.abc import Callable


class CallbackMap[I]:
    def __init__(self):
        self.d: dict[int, Callable[[I], None]] = {}
        self.key_counter = 0

    def add(self, callback: Callable[[I], None]) -> int:
        callback_key = self.key_counter
        self.d[callback_key] = callback
        self.key_counter += 1
        return callback_key

    def remove(self, key):
        del self.d[key]

    def execute(self, data: I):
        for callback in self.d.values():
            callback(data)
