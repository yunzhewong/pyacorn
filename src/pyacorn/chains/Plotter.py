from dataclasses import dataclass
import queue
import threading
from typing import Callable

from matplotlib import pyplot as plt
import matplotlib
import numpy as np

from pyacorn.chains.base import Tail


@dataclass
class PlotValues:
    times: list[float]
    values: list[float]

class Plotter(Tail[PlotValues]):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue[PlotValues]()
        plt.ion()
        self.fig, self.ax = plt.subplots()
        x = np.linspace(0, 1, num=100)
        y = np.zeros(x.shape)
        self.line, = self.ax.plot(x, y, 'b-')
        print(matplotlib.get_backend())

    def execute(self, data: PlotValues):
        self.queue.put(item=data)

    def block(self, should_stop: Callable[[], bool]):
        while not should_stop():
            try:
                plot_values = self.queue.get(timeout=0.1)
                self.line.set_xdata(plot_values.times)
                self.ax.set_xlim(left=min(plot_values.times), right=max(plot_values.times))
                self.ax.set_ylim(bottom=min(plot_values.values), top=max(plot_values.values))
                self.line.set_ydata(plot_values.values)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                plt.pause(1/60)
            except queue.Empty:
                pass

    def show(self):
        plt.ioff()
        plt.show()

