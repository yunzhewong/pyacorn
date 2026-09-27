from dataclasses import dataclass

from pyacorn.protocols import chainable
from pyacorn.utils import CallbackMap

@dataclass
class Packet():
    start_time: float
    values: list[float]

class UntimestampedStreamPacketizer():
    def __init__(self, sample_period_s: float):
        self.callback_map: CallbackMap[Packet] = CallbackMap()
        self.sample_period_s = sample_period_s
        self.running_count = 0

    def chain(self, item: chainable.Upstream[Packet]):
        self.callback_map.add(item.execute)

    def execute(self, data: list[float]):
        time = self.running_count * self.sample_period_s
        self.running_count += len(data)
        packet = Packet(start_time=time, values=data)
        self.callback_map.execute(packet)

