from dataclasses import dataclass
import math
import time
from numpy.typing import NDArray

import numpy as np

from pyacorn.chains.Batcher import Batcher
from pyacorn.chains.Plotter import Plotter, PlotValues
from pyacorn.chains.Buffer import Buffer
from pyacorn.chains.lambdas import Lambda
from pyacorn.serial_adapter import Packet

import pyacorn.oscilloscopes.fast_pico as fast_pico


INTRA_PACKET_DOWNSAMPLE_DECIMATION = 2000
BATCHER_SIZE = 10
VIEWING_SIZE_S = 10

BUFFER_SIZE = int(fast_pico.SAMPLES_PER_SECOND / INTRA_PACKET_DOWNSAMPLE_DECIMATION / BATCHER_SIZE * VIEWING_SIZE_S)


@dataclass
class SampleMetadata:
    start_time: float
    spacing_s: float

if __name__ == "__main__":
    def convert_to_values(packet: Packet[fast_pico.Metadata, bytes]) -> Packet[fast_pico.Metadata, NDArray[np.uint8]]:
        values = np.frombuffer(packet.data, dtype=fast_pico.DTYPE, count=fast_pico.VALS_PER_PACKET)
        return Packet(metadata=packet.metadata, data=values)

    def intra_packet_downsample(packet: Packet[fast_pico.Metadata, NDArray[np.uint8]]) -> Packet[SampleMetadata, NDArray[np.uint8]]:
        downsampled_spacing_s = fast_pico.SPACING_S * INTRA_PACKET_DOWNSAMPLE_DECIMATION
        downsampled_count = math.floor(len(packet.data) / INTRA_PACKET_DOWNSAMPLE_DECIMATION)
        downsampled_values: NDArray[np.uint8] = np.empty(downsampled_count, dtype=np.uint8)
        for i in range(downsampled_count):
            downsampled_values[i] = packet.data[i * INTRA_PACKET_DOWNSAMPLE_DECIMATION]
        start_time = packet.metadata.start_sample * fast_pico.SPACING_S
        return Packet(metadata=SampleMetadata(start_time=start_time, spacing_s=downsampled_spacing_s), data=downsampled_values)

    def inter_packet_downsample(packets: list[Packet[SampleMetadata, NDArray[np.uint8]]]) -> list[Packet[SampleMetadata, NDArray[np.uint8]]]:
        return [packets[0]]

    def flatten(packets: list[Packet[SampleMetadata, NDArray[np.uint8]]]) -> Packet[SampleMetadata, NDArray[np.uint8]]:
        return packets[0]

    def to_plot_values(packets: list[Packet[SampleMetadata, NDArray[np.uint8]]]) -> PlotValues:
        total_data = 0
        for packet in packets:
            total_data += len(packet.data)

        times: NDArray[np.float64] = np.zeros(total_data, dtype=np.float64) 
        values: NDArray[np.float64] = np.zeros(total_data, dtype=np.float64) 
        run_index: int = 0
        for packet in packets:
            stop_index = run_index + len(packet.data)
            times[run_index:stop_index] = np.arange(len(packet.data)) * packet.metadata.spacing_s + packet.metadata.start_time
            values[run_index:stop_index] = packet.data * fast_pico.SCALE_FACTOR
            run_index = stop_index
        return PlotValues(times=times, values=values)

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    to_values_lambda = Lambda(func=convert_to_values) 
    intra_downsample_lambda = Lambda(func=intra_packet_downsample)
    batcher = Batcher(batch_size=BATCHER_SIZE)
    inter_downsample_lambda = Lambda(func=inter_packet_downsample)
    flatten_lambda = Lambda(func=flatten)
    buffer = Buffer[Packet[SampleMetadata, NDArray[np.uint8]]](max_size=BUFFER_SIZE)
    to_plotvalues_lambda = Lambda(func=to_plot_values)
    plotter = Plotter()

    oscilloscope.chain(to_values_lambda)
    to_values_lambda.chain(intra_downsample_lambda)
    intra_downsample_lambda.chain(batcher)
    batcher.chain(inter_downsample_lambda)
    inter_downsample_lambda.chain(flatten_lambda)
    flatten_lambda.chain(buffer)
    buffer.chain(to_plotvalues_lambda)
    to_plotvalues_lambda.chain(plotter)
    
    oscilloscope.start()

    start_time = time.time()
    plotter.block(should_stop=lambda: time.time() - start_time > 20)

    oscilloscope.stop()

    plotter.show()
