import math

from pyacorn.chains import Body, Batcher, Buffer, Lambda
import pyacorn.chains.protocol as chainable
from pyacorn.serial_adapter import Packet

from .base import DTYPES, CAPTURE_BUFFER_SIZE, Oscilloscope as BaseOscilloscope, Metadata, BasicDataPackerSettings, SampleMetadata
import numpy as np
import numpy.typing as npt

SAMPLES_PER_SECOND = 500_000
BYTES_PER_FLOAT = 1
SCALE_FACTOR = 3.3 / (1 << 8)
MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 3.3
DTYPE = DTYPES[BYTES_PER_FLOAT]

SPACING_S = 1 / SAMPLES_PER_SECOND
VALS_PER_PACKET = int(CAPTURE_BUFFER_SIZE / BYTES_PER_FLOAT)

class Oscilloscope(BaseOscilloscope):
    pass

class BasicDataPacker(Body[Packet[Metadata, bytes], Packet[SampleMetadata, npt.NDArray[np.float32]]]):
    def __init__(self, settings: BasicDataPackerSettings):
        readings_in_raw_packet = CAPTURE_BUFFER_SIZE / BYTES_PER_FLOAT
        readings_in_data_packet = math.floor(settings.packets_per_update * readings_in_raw_packet / settings.downsample_multiplier)
        readings_spacing = SPACING_S * settings.downsample_multiplier
        readings_in_buffer = settings.plot_duration / readings_spacing
        buffer_size = math.ceil(readings_in_buffer / readings_in_data_packet)

        def to_data_packet(packets: list[Packet[Metadata, bytes]]) -> Packet[SampleMetadata, npt.NDArray[np.float32]]:
            total_values = 0
            for packet in packets:
                total_values += len(packet.data)

            start_time = packets[0].metadata.start_sample * SPACING_S
            spacing_s = SPACING_S * settings.downsample_multiplier
            downsampled_count = math.floor(total_values / settings.downsample_multiplier)
            int_values = np.zeros(downsampled_count, dtype=np.uint8)

            value_index = 0
            running_index = 0
            for packet in packets:
                packet_values = np.frombuffer(packet.data, dtype=DTYPE, count=VALS_PER_PACKET)
                while running_index < len(packet_values):
                    int_values[value_index] = packet_values[running_index]
                    value_index += 1
                    running_index += settings.downsample_multiplier            
                running_index -= len(packet_values)

            float_values = int_values * SCALE_FACTOR
            return Packet(metadata=SampleMetadata(start_time=start_time, spacing_s=spacing_s), data=float_values)


        batcher = Batcher[Packet[Metadata, bytes]](batch_size=settings.packets_per_update)
        to_data_lambda = Lambda(func=to_data_packet) 
        buffer = Buffer[Packet[SampleMetadata, npt.NDArray[np.float32]]](max_size=buffer_size)

        batcher.chain(to_data_lambda)
        to_data_lambda.chain(buffer)

        self.batcher = batcher
        self.buffer = buffer

    def chain(self, item: chainable.Upstream):
        self.buffer.chain(item)
        return item

    def execute(self, data: Packet[Metadata, bytes]):
        self.batcher.execute(data)