from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from pyacorn.chains.base import Tail


@dataclass
class Values:
    timestamped_values: npt.NDArray[
        np.float32
    ]  # N x (1 + number_of_columns), first column is time in seconds


class CSVWriter(Tail[Values]):
    def __init__(self, filepath: str, column_names: list[str]):
        self.column_names = column_names
        with open(filepath, "w") as f:
            f.write(f"Time (s), {' ,'.join(column_names)}\n")
        self.append_file = open(filepath, "a")

    def execute(self, data: Values):
        np.savetxt(self.append_file, data.timestamped_values, delimiter=",", fmt="%.6f")

    def close(self):
        self.append_file.close()
