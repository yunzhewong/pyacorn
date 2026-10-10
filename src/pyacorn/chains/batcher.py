from typing import final

from .base import Body


@final
class Batcher[T](Body[T, list[T]]):
    def __init__(self, batch_size: int):
        super().__init__()
        self.batch_size = batch_size
        self.buffer: list[T] = []

    def execute(self, data: T):
        self.buffer.append(data)
        if len(self.buffer) < self.batch_size:
            return
        self.callback_map.execute(self.buffer[: self.batch_size])
        self.buffer = self.buffer[self.batch_size :]
