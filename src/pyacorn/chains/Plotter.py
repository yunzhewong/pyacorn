from dataclasses import dataclass
import threading
import time
from typing import Callable, Optional

from matplotlib import pyplot as plt
import numpy as np
from numpy.typing import NDArray
from pyacorn.chains.base import Tail

FRAME_LIMIT = 60
@dataclass
class PlotValues:
    times: NDArray[np.float64]
    values: NDArray[np.float64]

class Plotter(Tail[PlotValues]):
    def __init__(self, frames_per_second: int = FRAME_LIMIT):
        super().__init__()
        self._plot_values: Optional[PlotValues] = None
        self._lock = threading.Lock()
        self.seconds_per_frame = 1 / frames_per_second

        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_ylim(bottom=0, top=3.3)
        plt.pause(self.seconds_per_frame)

    def execute(self, data: PlotValues):
        with self._lock:
            self._plot_values = data

    def block(self, should_stop: Callable[[], bool]):
        while not should_stop():
            start_time = time.monotonic()

            with self._lock:   
                plot_values = self._plot_values
            if plot_values is not None:
                self.ax.set_xlim(left=np.min(plot_values.times), right=np.max(plot_values.times))
                self.line.set_xdata(plot_values.times)
                self.line.set_ydata(plot_values.values)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()

            elapsed_time = time.monotonic() - start_time
            extra_sleep = self.seconds_per_frame - elapsed_time
            if extra_sleep > 0:
                time.sleep(extra_sleep)

    def show(self):
        plt.ioff()
        plt.show()

