from pyacorn.chains.base import Tail


class Printer[T](Tail[T]):
    def execute(self, data: T):
        print(data)
