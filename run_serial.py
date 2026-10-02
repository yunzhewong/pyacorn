import queue
import threading
import time
from typing import Callable

import serial

from pyacorn.chains.base import Head
from pyacorn.chains.lambdas import Printer
from pyacorn.consumers.BaseStreamer import Packet, PacketGrouper

SCALE_FACTOR = 3.3 / (1 << 8)
def convert_to_voltage(packets: list[Packet]) -> list[Packet[list[float]]]:
    return [Packet(counter=packet.counter, data=[data_byte * SCALE_FACTOR for data_byte in packet.data]) for packet in packets]

class SerialConnection():
    def __init__(self, port: str, output_queue: queue.Queue[bytes]):
        self.port = port
        self.output_queue = output_queue

    def handle(self, abort_event: threading.Event):
        connection = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
        while not abort_event.is_set():
            data = connection.read(8192)   # blocks until timeout or newline
            self.output_queue.put(data)
        connection.close()

class PacketParser():
    def __init__(self, input_queue: queue.Queue[bytes], callback: Callable[[list[Packet[list[float]]]], None]):
        self.grouper = PacketGrouper()
        self.input_queue = input_queue
        self.callback = callback

    def handle(self, abort_event: threading.Event):
        while not abort_event.is_set():
            try:
                new_data = self.input_queue.get(block=False)
                packed_data = self.grouper.add_data(new_data)
                converted_data = convert_to_voltage(packets=packed_data)
                self.callback(converted_data)
            except queue.Empty:
                pass

class FastPicoOscilloscope(Head[list[Packet[list[float]]]]):
    def __init__(self, port: str):
        super().__init__()
        shared_queue = queue.Queue[bytes]()
        self.serial_connection = SerialConnection(port=port, output_queue=shared_queue)
        self.grouper = PacketParser(input_queue=shared_queue, callback=self.initiate)
        self._threads: list[threading.Thread] = []
        self._abort_event = threading.Event()

    def start(self):
        self._abort_event.clear()
        self._threads = [
            threading.Thread(target=self.serial_connection.handle, args=(self._abort_event, )),
            threading.Thread(target=self.grouper.handle, args=(self._abort_event, ))
        ]
        for thread in self._threads:
            thread.start()

    def stop_and_join(self):
        self._abort_event.set()
        for thread in self._threads:
            thread.join()

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