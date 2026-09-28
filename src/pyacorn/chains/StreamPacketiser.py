from dataclasses import dataclass

from pyacorn.protocols import chainable
from pyacorn.utils import CallbackMap

@dataclass
class Packet():
    running_count: float
    sample_period_s: float
    values: list[float]

@dataclass
class StreamPacketiserMemory():
    sample_period_s: float
    running_count: int

    def pack_from_stream(self, data: list[float]) -> Packet:
        running_count = self.running_count
        self.running_count += len(data)
        return Packet(running_count=running_count, sample_period_s=self.sample_period_s, values=data)

class StreamPacketiser():
    def __init__(self, sample_period_s: float):
        self.callback_map: CallbackMap[Packet] = CallbackMap()
        self._memory = StreamPacketiserMemory(sample_period_s=sample_period_s, running_count=0) 

    def chain(self, item: chainable.Upstream[Packet]):
        self.callback_map.add(item.execute)

    def execute(self, data: list[float]):
        packet = self._memory.pack_from_stream(data)
        self.callback_map.execute(packet)

