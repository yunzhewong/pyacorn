from dataclasses import dataclass
import threading
from typing import Optional

from pyacorn.chains.base import Head
from pyacorn.serial_adapter import ByteMetadata, Packet, RolloverCountHistory, SerialPacketHandler

CAPTURE_BUFFER_SIZE = 2000 
DTYPES = {1: "<u1", 2: "<u2", 4: "<u4", 8: "<u8"}  # little-endian, unsigned
MIN_VOLTAGE = 0
MAX_VOLTAGE = 3.3

@dataclass
class Metadata:
    start_sample: int

@dataclass
class SampleMetadata:
    start_time: float
    spacing_s: float

@dataclass
class Parameters():
    samples_per_second: int
    bytes_per_float: int
    
    @property
    def dtype(self) -> str:
        return DTYPES[self.bytes_per_float] 

    @property
    def scale_factor(self):
        return MAX_VOLTAGE / (1 << (8 * self.bytes_per_float))

    @property
    def spacing_s(self):
        return 1 / self.samples_per_second

    @property
    def values_per_packet(self):
        return int(CAPTURE_BUFFER_SIZE / self.bytes_per_float)

@dataclass
class BasicDataPackerSettings():
    downsample_multiplier: int
    packets_per_update: int

CONTINUOUS_SENTINEL = -1
class AcquisitionMode:
    def __init__(self, frames: int):
        self.frames = frames

    def is_complete(self, frame_count: int):
        if self.frames == CONTINUOUS_SENTINEL:
            return False
        return frame_count >= self.frames

    @staticmethod
    def single():
        return AcquisitionMode(frames=1)

    @staticmethod
    def multiple(frames: int):
        return AcquisitionMode(frames=frames)

    @staticmethod
    def continuous():
        return AcquisitionMode(frames=CONTINUOUS_SENTINEL)

class Oscilloscope(Head[Packet[Metadata, bytes]]):
    def __init__(self, port: str):
        super().__init__()
        self._reader = SerialPacketHandler(port=port, capture_buffer_size=CAPTURE_BUFFER_SIZE, on_packet=self._handle_packet)
        self._rollover_count_history = RolloverCountHistory()

        self._complete_event = threading.Event()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._acquisition_mode = AcquisitionMode.continuous()
        self._counter: int = 0

    def acquire(self, acquisition_mode: AcquisitionMode):
        with self._lock:
            self._acquisition_mode = acquisition_mode
            self._counter = 0 
        self._complete_event.clear()
        self._reader.start()

        def stop_handle():
            self._complete_event.wait()
            self._reader.stop()

        self._thread = threading.Thread(target=stop_handle)
        self._thread.start()

    def stop(self):
        self._complete_event.set()
        if self._thread:
            self._thread.join()

    def is_complete(self):
        return self._complete_event.is_set()

    def _handle_packet(self, packet: Packet[ByteMetadata, bytes]):
        if self._complete_event.is_set():
            return
        packet_counter = self._rollover_count_history.account_for_rollover(packet.metadata.rolling_packet_counter)
        start_sample = packet_counter * CAPTURE_BUFFER_SIZE
        self.initiate(Packet(metadata=Metadata(start_sample=start_sample), data=packet.data))
        with self._lock:
            self._counter += 1
            if self._acquisition_mode.is_complete(frame_count=self._counter):
                self._complete_event.set()