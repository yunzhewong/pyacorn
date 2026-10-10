import math
from dataclasses import dataclass

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
class Parameters:
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
    def samples_per_packet(self):
        return int(CAPTURE_BUFFER_SIZE / self.bytes_per_float)

    @property
    def packets_per_second(self):
        return self.samples_per_second / self.samples_per_packet


FRAME_RATE = 60


@dataclass
class BasicChainSettings:
    downsample_multiplier: int
    frame_rate: float = FRAME_RATE

    def calc_packets_per_update(self, parameters: Parameters):
        return math.floor(parameters.packets_per_second / self.frame_rate)


CONTINUOUS_SENTINEL = -1


class AcquisitionMode:
    def __init__(self, frames: int):
        self.frames = frames

    def is_complete(self, frame_count: int):
        if self.frames == CONTINUOUS_SENTINEL:
            return False
        return frame_count >= self.frames

    @staticmethod
    def until_frames_captured(min_frames: int, settings: BasicChainSettings, parameters: Parameters):
        packets_per_update = settings.calc_packets_per_update(parameters=parameters)
        actual_frames = math.ceil(min_frames / packets_per_update) * packets_per_update
        return AcquisitionMode(frames=actual_frames)

    @staticmethod
    def continuous():
        return AcquisitionMode(frames=CONTINUOUS_SENTINEL)
