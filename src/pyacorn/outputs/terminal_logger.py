
import time
from pyacorn.chains.base import Tail

class TerminalLogger(Tail[str]):
    def __init__(self):
        super().__init__()
        self.written_characters = 0

    def execute(self, data: str):
        print("\b" * self.written_characters + " " * self.written_characters + "\b" * self.written_characters, end="")
        write_data = f"{time.time():.2f}: {data}"
        print(write_data, end="", flush=True)
        self.written_characters = len(write_data)

