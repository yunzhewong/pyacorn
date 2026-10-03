from dataclasses import dataclass
import queue
import threading
import time
from typing import Callable

import serial

from pyacorn.chains.base import Head
from pyacorn.chains.lambdas import Printer
from pyacorn.consumers.BaseStreamer import CAPTURE_BUFFER_SIZE, ByteMetadata, Packet, SerialBuffer


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

class PacketBuffer():
    def __init__(self, input_queue: queue.Queue[bytes], on_packet: Callable[[Packet[ByteMetadata, bytes]], None]):
        self.buffer = SerialBuffer()
        self.input_queue = input_queue
        self.callback = on_packet

    def handle(self, abort_event: threading.Event):
        while not abort_event.is_set():
            try:
                new_data = self.input_queue.get(block=False)
                received_packets = self.buffer.handle_new_data(new_data)
                for packet in received_packets:
                    self.callback(packet)
            except queue.Empty:
                pass

class SerialPacketReader():
    def __init__(self, port: str, on_packet: Callable[[Packet[ByteMetadata, bytes]]]):
        shared_queue = queue.Queue[bytes]()
        self.serial_connection = SerialConnection(port=port, output_queue=shared_queue)
        self.packet_buffer = PacketBuffer(input_queue=shared_queue, on_packet=on_packet)
        self._threads: list[threading.Thread] = []
        self._abort_event = threading.Event()

    def start(self):
        self._abort_event.clear()
        self._threads = [
            threading.Thread(target=self.serial_connection.handle, args=(self._abort_event, )),
            threading.Thread(target=self.packet_buffer.handle, args=(self._abort_event, ))
        ]
        for thread in self._threads:
            thread.start()

    def stop(self):
        self._abort_event.set()
        for thread in self._threads:
            thread.join()

ROLLOVER_VALUE = 1 << 8
class RolloverCountHistory:
    def __init__(self):
        self.last_rollover = -1
        self.last_accounted = -1

    def account_for_rollover(self, rollover_count: int) -> int:
        if self.last_rollover == -1 or self.last_accounted == -1:
            self.last_rollover = rollover_count
            self.last_accounted = rollover_count
            return self.last_accounted

        rollover_difference = (rollover_count + ROLLOVER_VALUE - self.last_rollover) % ROLLOVER_VALUE
        self.last_rollover = rollover_count
        self.last_accounted += rollover_difference
        return self.last_accounted

@dataclass(frozen=True)
class FastPicoMetadata:
    start_sample: int
    bytes_per_float: int = 1
    spacing_s: float = 3.3 / (1 << 8)
    scale_factor: float = 1 / 500_000

class FastPicoOscilloscope(Head[Packet[FastPicoMetadata, bytes]]):
    def __init__(self, port: str):
        super().__init__()
        self.reader = SerialPacketReader(port=port, on_packet=self._handle_packet)
        self.rollover_count_history = RolloverCountHistory()

    def start(self):
        self.reader.start()

    def stop(self):
        self.reader.stop()

    def _handle_packet(self, packet: Packet[ByteMetadata, bytes]):
        packet_counter = self.rollover_count_history.account_for_rollover(packet.metadata.rolling_packet_counter)
        start_sample = packet_counter * CAPTURE_BUFFER_SIZE
        self.initiate(Packet(metadata=FastPicoMetadata(start_sample=start_sample), data=packet.data))

if __name__ == "__main__":
    oscilloscope = FastPicoOscilloscope(port="/dev/ttyACM0")
    oscilloscope.chain(Printer(transform=lambda ps: ps.data[0]))
    oscilloscope.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    oscilloscope.stop()