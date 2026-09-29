import math
import queue
import time

import matplotlib

from pyacorn.chains.Buffer import Buffer
from pyacorn.chains.Lambda import Lambda
from pyacorn.chains.Plotter import PlotValues, Plotter
from pyacorn.chains.StreamPacketiser import Packet, StreamPacketiser
from pyacorn import sim
from pyacorn.utils import CallbackMap
import matplotlib.pyplot as plt
import numpy as np

def func(t: float):
    return math.sin(2*math.pi*t)

stream = sim.Stream(func, sample_period_s=0.01, output_period_s=1/30, callback_map=CallbackMap())
packetiser = StreamPacketiser(sample_period_s=0.01)
buffer = Buffer(max_size=60)

def expand(packets: list[Packet]) -> PlotValues:
    times = []
    values = []
    
    for packet in packets:
        for i, value in enumerate(packet.values):
            index = packet.running_count + i
            time = index * packet.sample_period_s
            times.append(time)
            values.append(value)

    print(PlotValues(times=times, values=values))
    return PlotValues(times=times, values=values)

expander = Lambda(func=expand)
plotter = Plotter()

stream.chain(packetiser)
packetiser.chain(buffer)
buffer.chain(expander)
expander.chain(plotter)

stream.start()

start_time = time.time()
def should_stop():
    return time.time() - start_time > 5     

plotter.block(should_stop=should_stop)

stream.stop_and_join()
plt.ioff()
plt.show()
plotter.show()