from dataclasses import dataclass

from pyacorn.chains.base import Tail


@dataclass
class Values:
    time: float
    text: str

    def to_log_data(self):
        return f"({self.time:.2f}) {self.text}"


class TerminalLogger(Tail[Values]):
    def __init__(self):
        super().__init__()
        self.written_characters = 0

    def execute(self, data: Values):
        print(
            "\b" * self.written_characters + " " * self.written_characters + "\b" * self.written_characters,
            end="",
        )
        log_data = data.to_log_data()
        print(log_data, end="", flush=True)
        self.written_characters = len(log_data)
