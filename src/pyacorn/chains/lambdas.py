from typing import Any, Callable

from pyacorn.chains.Plotter import PlotValues
from pyacorn.chains.StreamPacketiser import Packet
from pyacorn.chains.base import Body


class Lambda[I, O](Body[I, O]):
    def __init__(self, func: Callable[[I], O]):
        super().__init__()
        self.func = func

    def operate(self, data: I):
        return self.func(data)

def expand_packet(packets: list[Packet]) -> PlotValues:
    times = []
    values = []
    for packet in packets:
        for i, value in enumerate(packet.values):
            index = packet.running_count + i
            time = index * packet.sample_period_s
            times.append(time)
            values.append(value)
    return PlotValues(times=times, values=values)

class PacketExpander(Lambda[list[Packet], PlotValues]):
    def __init__(self) -> None:
        super().__init__(func=expand_packet)

class Printer[T](Lambda[T, None]):
    def __init__(self, transform: Callable[[T], Any] = lambda x: x):
        super().__init__(func=lambda x: print(transform(x)))