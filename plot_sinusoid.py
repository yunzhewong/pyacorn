import math
import time

from pyacorn.chains.Buffer import Buffer
from pyacorn.chains.lambdas import PacketExpander
from pyacorn.chains.Plotter import Plotter
from pyacorn.chains.StreamPacketiser import Packet, StreamPacketiser
from pyacorn import sim

def func(t: float):
    return math.sin(2*math.pi*t)

stream = sim.Stream(func, sample_period_s=0.001, output_period_s=1/60)
packetiser = StreamPacketiser(sample_period_s=0.001)
buffer = Buffer[Packet](max_size=60)
expander = PacketExpander()
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
plotter.show()