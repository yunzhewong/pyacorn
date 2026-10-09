from pyacorn.chains.base import Tail


class CSVWriter(Tail[]):
    def __init__(self, filepath: str, columns: int):
        self.file = open(filepath, mode="w")
        self.file.write("Time(s), Value")

    def execute():

    def close(self):
        self.file.close()