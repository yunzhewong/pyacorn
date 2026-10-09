from dataclasses import dataclass
import signal
import threading
import time
from typing import Callable

from matplotlib import pyplot as plt
import numpy as np
from numpy.typing import NDArray
from pyacorn.chains.base import Tail
from pyacorn.oscilloscopes.base import Oscilloscope

FRAME_LIMIT = 60

@dataclass
class Values:
    times: NDArray[np.float32]
    values: NDArray[np.float32]

@dataclass
class Attributes:
    values: Values | None
    lock: threading.Lock
    seconds_per_frame: float

    @staticmethod
    def create(frames_per_second: float):
        return Attributes(values=None, lock=threading.Lock(), seconds_per_frame=1 / frames_per_second)

    def change_values(self, new_values: Values):
        with self.lock:
            self.values = new_values

    def get_values(self):
        with self.lock:
            return self.values

    def calc_sleep_duration(self, elapsed_time: float):
        duration = self.seconds_per_frame - elapsed_time
        if duration > 0:
            return duration
        return 0

class Plotter(Tail[Values]):
    def __init__(self, min: float, max: float, frames_per_second: int = FRAME_LIMIT):
        super().__init__()
        self._attributes = Attributes.create(frames_per_second=frames_per_second) 

        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_ylim(bottom=min, top=max)
        plt.pause(self._attributes.seconds_per_frame)

    def execute(self, data: Values):
        self._attributes.change_values(data)

    def block(self, should_stop: Callable[[], bool]):
        while not should_stop():
            start_time = time.monotonic()

            plot_values = self._attributes.get_values()
            if plot_values is not None:
                self.ax.set_xlim(left=float(np.min(plot_values.times)), right=float(np.max(plot_values.times)))
                self.line.set_xdata(plot_values.times)
                self.line.set_ydata(plot_values.values)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()

            time.sleep(self._attributes.calc_sleep_duration(elapsed_time=time.monotonic() - start_time))

    def show(self):
        print("Acquisition Complete - Close plot when done")
        plt.ioff()
        plt.show()



