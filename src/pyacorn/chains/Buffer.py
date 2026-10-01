from pyacorn.chains.base import Body


class Buffer[T](Body[T, list[T]]):
    def __init__(self, max_size: int):
        super().__init__()
        self.buffered_data: list[T] = []
        self.max_size = max_size

    def operate(self, data: T) -> list[T]:
        self.buffered_data.append(data)
        if len(self.buffered_data) > self.max_size:
            self.buffered_data = self.buffered_data[1:]
        return self.buffered_data