from dataclasses import dataclass
import queue
from typing import Callable

from matplotlib import pyplot as plt
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

    def execute(self, data: PlotValues):
        print("sent")
        self.queue.put(item=data)

    def block(self, should_stop: Callable[[], bool]):
        while not should_stop():
            last = None
            try:
                while True:  
                    last = self.queue.get()
                    print("received")
            except queue.Empty:
                pass

            if last is not None:
                self.ax.set_xlim(left=min(last.times), right=max(last.times))
                self.ax.set_ylim(bottom=min(last.values), top=max(last.values))

                print(min(last.values), max(last.values))
                self.line.set_xdata(last.times)
                self.line.set_ydata(last.values)
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
            plt.pause(1/60)

    def show(self):
        plt.ioff()
        plt.show()

