import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass

import serial

from pyacorn.chains.base import Head

DELIMITER = 0xFF


def crc8(data: bytes, init: int = 0xFF, poly: int = 0x07) -> int:
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


# _TABLE = []
# for i in range(256):
#     c = i
#     for _ in range(8):
#         c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
#     _TABLE.append(c)

# def crc8_fast(data: bytes, init: int = 0xFF) -> int:
#     crc = init
#     for byte in data:
#         crc = _TABLE[crc ^ byte]
#     return crc


@dataclass
class ByteMetadata:
    rolling_packet_counter: int


@dataclass
class Packet[M, T]:
    metadata: M
    data: T


class PacketBuffer(Head[list[Packet[ByteMetadata, bytes]]]):
    def __init__(self, capture_buffer_size: int):
        super().__init__()
        self.buffer = b""
        self.capture_buffer_size = capture_buffer_size

    def handle_new_data(self, new_data: bytes):
        self.buffer += new_data
        output: list[Packet[ByteMetadata, bytes]] = []
        while len(self.buffer) >= 3 + self.capture_buffer_size:
            skip = 0
            while self.buffer[skip] != DELIMITER and skip < len(self.buffer):
                skip += 1

            if skip > len(self.buffer):
                self.buffer = b""
                break

            self.buffer = self.buffer[skip:]
            if len(self.buffer) < 3 + self.capture_buffer_size:
                break

            buffer_bytes = self.buffer[: 3 + self.capture_buffer_size]
            self.buffer = self.buffer[3 + self.capture_buffer_size :]

            packet_counter = buffer_bytes[1]
            data_bytes = buffer_bytes[2 : 2 + self.capture_buffer_size]
            crc = buffer_bytes[2 + self.capture_buffer_size]
            if crc8(data_bytes) != crc:
                continue
            output.append(
                Packet(
                    metadata=ByteMetadata(rolling_packet_counter=packet_counter),
                    data=data_bytes,
                )
            )
        return output


class SerialConnection:
    def __init__(self, port: str, output_queue: queue.Queue[bytes]):
        self.port = port
        self.output_queue = output_queue

    def handle(self, abort_event: threading.Event):
        connection = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
        while not abort_event.is_set():
            data = connection.read(8192)  # blocks until timeout or newline
            self.output_queue.put(data)
        connection.close()


class PacketHandler:
    def __init__(
        self,
        capture_buffer_size: int,
        input_queue: queue.Queue[bytes],
        on_packet: Callable[[Packet[ByteMetadata, bytes]], None],
    ):
        self.buffer = PacketBuffer(capture_buffer_size=capture_buffer_size)
        self.input_queue = input_queue
        self.on_packet = on_packet

    def handle(self, abort_event: threading.Event):
        while not abort_event.is_set():
            try:
                new_data = self.input_queue.get(timeout=0.1)
                received_packets = self.buffer.handle_new_data(new_data)
                for packet in received_packets:
                    self.on_packet(packet)
            except queue.Empty:
                pass


class SerialPacketHandler:
    def __init__(
        self,
        port: str,
        capture_buffer_size: int,
        on_packet: Callable[[Packet[ByteMetadata, bytes]], None],
    ):
        shared_queue = queue.Queue[bytes]()
        self.serial_connection = SerialConnection(port=port, output_queue=shared_queue)
        self.packet_handler = PacketHandler(
            capture_buffer_size=capture_buffer_size,
            input_queue=shared_queue,
            on_packet=on_packet,
        )
        self._threads: list[threading.Thread] = []
        self._abort_event = threading.Event()

    def start(self):
        self._abort_event.clear()
        self._threads = [
            threading.Thread(
                target=self.serial_connection.handle, args=(self._abort_event,)
            ),
            threading.Thread(
                target=self.packet_handler.handle, args=(self._abort_event,)
            ),
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
            self.last_accounted = 0
            return self.last_accounted

        rollover_difference = (
            rollover_count + ROLLOVER_VALUE - self.last_rollover
        ) % ROLLOVER_VALUE
        self.last_rollover = rollover_count
        self.last_accounted += rollover_difference
        return self.last_accounted
