import math

from pyacorn.chains import Body, Batcher, Lambda
import pyacorn.chains.protocol as chainable
from pyacorn.serial_adapter import Packet

from .base import Oscilloscope as BaseOscilloscope, Metadata, BasicDataPackerSettings, Parameters, SampleMetadata
import numpy as np
import numpy.typing as npt

PARAMETERS = Parameters(samples_per_second=500_000, bytes_per_float=1)

class Oscilloscope(BaseOscilloscope):
    pass

class BasicDataPacker(Body[Packet[Metadata, bytes], Packet[SampleMetadata, npt.NDArray[np.float32]]]):
    def __init__(self, settings: BasicDataPackerSettings):
        def to_data_packet(packets: list[Packet[Metadata, bytes]]) -> Packet[SampleMetadata, npt.NDArray[np.float32]]:
            total_values = 0
            for packet in packets:
                total_values += len(packet.data)

            start_time = packets[0].metadata.start_sample * PARAMETERS.spacing_s
            spacing_s = PARAMETERS.spacing_s * settings.downsample_multiplier
            downsampled_count = math.floor(total_values / settings.downsample_multiplier)
            int_values = np.zeros(downsampled_count, dtype=np.uint8)

            value_index = 0
            running_index = 0
            for packet in packets:
                packet_values = np.frombuffer(packet.data, dtype=PARAMETERS.dtype, count=PARAMETERS.values_per_packet)
                while running_index < len(packet_values):
                    int_values[value_index] = packet_values[running_index]
                    value_index += 1
                    running_index += settings.downsample_multiplier            
                running_index -= len(packet_values)

            float_values = int_values * PARAMETERS.scale_factor
            return Packet(metadata=SampleMetadata(start_time=start_time, spacing_s=spacing_s), data=float_values)


        self.batcher = Batcher[Packet[Metadata, bytes]](batch_size=settings.packets_per_update)
        self.to_data_lambda = Lambda(func=to_data_packet) 

        self.batcher.chain(self.to_data_lambda)

    def chain(self, item: chainable.Upstream):
        self.to_data_lambda.chain(item)
        return item

    def execute(self, data: Packet[Metadata, bytes]):
        self.batcher.execute(data)