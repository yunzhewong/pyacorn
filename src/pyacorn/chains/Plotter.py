from dataclasses import dataclass
import queue
import time
from typing import Callable

from matplotlib import pyplot as plt
import numpy as np
from numpy.typing import NDArray
from pyacorn.chains.base import Tail


@dataclass
class PlotValues:
    times: NDArray[np.float64]
    values: NDArray[np.float64]

class Plotter(Tail[PlotValues]):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue[PlotValues]()

        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_xlim(left=0, right=2)
        self.ax.set_ylim(bottom=0, top=3.3)
        plt.pause(0.1)

        self.last_time = time.time()

    def execute(self, data: PlotValues):
        current_time = time.time()
        if current_time - self.last_time < 1/60:
            return
        self.queue.put(item=data)
        self.last_time = current_time

    def block(self, should_stop: Callable[[], bool]):
        while not should_stop():
            try:
                plot_values = self.queue.get(timeout=1/60)

                self.line.set_xdata(np.asarray(plot_values.times))
                self.line.set_ydata(plot_values.values)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
            except queue.Empty:
                pass

    def show(self):
        plt.ioff()
        plt.show()

