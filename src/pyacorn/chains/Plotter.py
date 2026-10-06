from dataclasses import dataclass
import queue
import threading
import time
from typing import Callable, Optional

from matplotlib import pyplot as plt
import numpy as np
from numpy.typing import NDArray
from pyacorn.chains.base import Tail

FRAME_RATE = 60
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
        self.ax.set_ylim(bottom=0, top=3.3)
        plt.pause(0.1)

    def execute(self, data: PlotValues):
        self.queue.put(data)

    def block(self, should_stop: Callable[[], bool]):
        while not should_stop():
            try:
                plot_values = self.queue.get(timeout=1/60)

                self.ax.set_xlim(left=np.min(plot_values.times), right=np.max(plot_values.times))
                self.line.set_xdata(plot_values.times)
                self.line.set_ydata(plot_values.values)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
            except queue.Empty:
                pass

    def show(self):
        plt.ioff()
        plt.show()

