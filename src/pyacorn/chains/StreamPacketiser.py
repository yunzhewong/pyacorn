from dataclasses import dataclass

from pyacorn.chains.base import Body

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

class StreamPacketiser(Body[list[float], Packet]):
    def __init__(self, sample_period_s: float):
        super().__init__()
        self._memory = StreamPacketiserMemory(sample_period_s=sample_period_s, running_count=0) 

    def operate(self, data: list[float]) -> Packet:
        return self._memory.pack_from_stream(data)