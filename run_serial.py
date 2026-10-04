from dataclasses import dataclass
import math
import queue
import threading
import time
from typing import Callable
from numpy.typing import NDArray

import numpy as np
import serial

from pyacorn.chains.Plotter import Plotter, PlotValues
from pyacorn.chains.Buffer import Buffer
from pyacorn.chains.base import Head
from pyacorn.chains.lambdas import Lambda, Printer
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
        self.on_packet = on_packet

    def handle(self, abort_event: threading.Event):
        while not abort_event.is_set():
            try:
                new_data = self.input_queue.get(block=False)
                received_packets = self.buffer.handle_new_data(new_data)
                for packet in received_packets:
                    self.on_packet(packet)
            except queue.Empty:
                pass

class SerialPacketReader():
    def __init__(self, port: str, on_packet: Callable[[Packet[ByteMetadata, bytes]], None]):
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

FAST_PICO_BYTES_PER_FLOAT = 1
FAST_PICO_SPACING_S = 1 / 500_000
FAST_PICO_SCALE_FACTOR = 3.3 / (1 << 8)
@dataclass(frozen=True)
class FastPicoMetadata:
    start_sample: int
    bytes_per_float: int = FAST_PICO_BYTES_PER_FLOAT
    spacing_s: float = FAST_PICO_SPACING_S
    scale_factor: float = FAST_PICO_SCALE_FACTOR

@dataclass
class SampleMetadata:
    start_time: float
    spacing_s: float

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

_DTYPES = {1: "<u1", 2: "<u2", 4: "<u4", 8: "<u8"}  # little-endian, unsigned

if __name__ == "__main__":
    convert_time: list[float] = []
    downsample_time: list[float] = []
    to_values_time: list[float] = []


    def convert_to_values(packet: Packet[FastPicoMetadata, bytes]) -> Packet[FastPicoMetadata, NDArray[np.float64]]:
        start_time = time.time()

        number_of_values = round(CAPTURE_BUFFER_SIZE / packet.metadata.bytes_per_float)
        
        values = np.frombuffer(packet.data, dtype=_DTYPES[packet.metadata.bytes_per_float], count=number_of_values)
        # values = raw * packet.metadata.scale_factor  # float64 array
        # values = raw * 1.0  # float64 array
        convert_time.append(time.time() - start_time)
        return Packet(metadata=packet.metadata, data=values)

    def downsample(packet: Packet[FastPicoMetadata, list[float]]) -> Packet[SampleMetadata, list[float]]:
        cycle_time = time.time()
        SAMPLES = 10
        downsampled_spacing_s = packet.metadata.spacing_s * SAMPLES
        downsampled_count = int(len(packet.data) / SAMPLES)
        downsampled_values: list[float] = [packet.data[i * SAMPLES] for i in range(downsampled_count)] 
        start_time = packet.metadata.start_sample * packet.metadata.spacing_s
        downsample_time.append(time.time() - cycle_time)
        return Packet(metadata=SampleMetadata(start_time=start_time, spacing_s=downsampled_spacing_s), data=downsampled_values)

    def to_plot_values(packets: list[Packet[SampleMetadata, list[float]]]) -> PlotValues:
        start_time = time.time()
        times: list[float] = []
        values: list[float] = []
        
        for packet in packets:
            new_times = [i * packet.metadata.spacing_s + packet.metadata.start_time for i in range(len(packet.data))]
            times += new_times
            values += packet.data
        to_values_time.append(time.time() - start_time)
        return PlotValues(times=times, values=values)

    oscilloscope = FastPicoOscilloscope(port="/dev/ttyACM0")
    to_values_lambda = Lambda(func=convert_to_values) 
    downsample_lambda = Lambda(func=downsample)
    buffer = Buffer(max_size=1) # one second of buffer
    to_plotvalues_lambda = Lambda(func=to_plot_values)
    # plotter = Plotter()
    printer = Printer()

    oscilloscope.chain(to_values_lambda)
    to_values_lambda.chain(downsample_lambda)
    downsample_lambda.chain(buffer)
    buffer.chain(to_plotvalues_lambda)
    to_plotvalues_lambda.chain(printer)
    # to_plotvalues_lambda.chain(plotter)
    
    oscilloscope.start()

    start_time = time.time()
    def should_stop():
        return time.time() - start_time  > 2
    print(f"Started: {time.time()}")
    while not should_stop():
        pass
    # plotter.block(should_stop=should_stop)
    print(f"Stopped: {time.time()}")

    oscilloscope.stop()

    print(sum(convert_time), len(convert_time))
    print(sum(downsample_time), len(downsample_time))
    print(sum(to_values_time), len(to_values_time))
    # plotter.show()    