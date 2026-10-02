import queue
import threading
import time
from typing import Callable, Optional

from pyacorn.chains.base import Head
from pyacorn.chains.lambdas import Lambda, Printer
from pyacorn.consumers.BaseStreamer import Packet, PacketGrouper
from pyacorn.consumers.SerialConsumer import SerialConsumer

SCALE_FACTOR = 3.3 / (1 << 8)
def convert_to_voltage(packets: list[Packet]) -> list[Packet[list[float]]]:
    return [Packet(counter=packet.counter, data=[data_byte * SCALE_FACTOR for data_byte in packet.data]) for packet in packets]


class FastGrouper():
    def __init__(self, consumer_queue: queue.Queue[bytes]):
        self.consumer_queue = consumer_queue
        self.grouper = PacketGrouper()

    def handle(self, abort_event: threading.Event, on_data: Callable[[list[Packet[list[float]]]], None]):
        while not abort_event.is_set():
            try:
                new_data = self.consumer_queue.get(block=False)
                packed_data = self.grouper.add_data(new_data)
                converted_data = convert_to_voltage(packets=packed_data)
                on_data(converted_data)
            except queue.Empty:
                pass

class FastPicoOscilloscope(Head[list[Packet[list[float]]]]):
    def __init__(self, port: str):
        super().__init__()
        self.consumer = SerialConsumer(port=port)
        self.grouper = FastGrouper(consumer_queue=self.consumer.output_queue)
        self._thread: Optional[threading.Thread] = None
        self._abort_event = threading.Event()

    def start(self):
        self.consumer.start()
        self._thread = threading.Thread(target=self.grouper.handle, args=(self._abort_event, self.initiate))
        self._thread.start()

    def stop_and_join(self):
        self._abort_event.set()
        self.consumer.stop_and_join()
        if self._thread is not None:
            self._thread.join()

if __name__ == "__main__":
    oscilloscope = FastPicoOscilloscope(port="/dev/ttyACM0")

    oscilloscope.chain(Printer(transform=lambda ps: ps[0].data[0]))
    oscilloscope.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    oscilloscope.stop_and_join()