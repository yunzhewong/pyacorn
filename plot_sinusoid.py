import math
import queue
import time

from pyacorn.chains.StreamPacketiser import StreamPacketiser
from pyacorn import sim
from pyacorn.utils import CallbackMap
import matplotlib.pyplot as plt
import numpy as np

def func(t: float):
    return math.sin(2*math.pi*t)

stream = sim.Stream(func, sample_period_s=0.01, output_period_s=0.1, callback_map=CallbackMap())
packetiser = StreamPacketiser(sample_period_s=0.01)
packetiser.callback_map.add(callback=print)
stream.chain(packetiser)

callback_map = CallbackMap()

data_queue = queue.Queue[list[float]]()
def callback(data: list[float]):
    data_queue.put(data)

callback_map.add(callback=callback)

plt.ion()
fig, ax = plt.subplots()
x = np.linspace(0, 1, num=100)
y = np.zeros(x.shape)
line, = ax.plot(x, y, 'b-')
ax.set_ylim(bottom=-1, top=1)

stream.start()

start_time = time.time()
while time.time() - start_time < 2:
    try:
        data = data_queue.get(timeout=0.1)
        line.set_ydata(data[:100])
        fig.canvas.draw()
        fig.canvas.flush_events()
    except queue.Empty:
        pass

stream.stop_and_join()
plt.ioff()
plt.show()