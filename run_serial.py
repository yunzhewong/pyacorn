from dataclasses import dataclass
import math
import time
from numpy.typing import NDArray

import numpy as np

from pyacorn.chains.Plotter import Plotter, PlotValues
from pyacorn.chains.Buffer import Buffer
from pyacorn.chains.lambdas import Lambda
from pyacorn.serial_adapter import Packet

import pyacorn.oscilloscopes.fast_pico as fast_pico

@dataclass
class SampleMetadata:
    start_time: float
    spacing_s: float


_DTYPES = {1: "<u1", 2: "<u2", 4: "<u4", 8: "<u8"}  # little-endian, unsigned

if __name__ == "__main__":
    def convert_to_values(packet: Packet[fast_pico.Metadata, bytes]) -> Packet[fast_pico.Metadata, NDArray[np.uint8]]:
        number_of_values = round(fast_pico.CAPTURE_BUFFER_SIZE/ packet.metadata.bytes_per_float)
        values = np.frombuffer(packet.data, dtype=_DTYPES[packet.metadata.bytes_per_float], count=number_of_values)
        return Packet(metadata=packet.metadata, data=values)

    def downsample(packet: Packet[fast_pico.Metadata, NDArray[np.uint8]]) -> Packet[SampleMetadata, NDArray[np.uint8]]:
        SAMPLES = 2000
        downsampled_spacing_s = packet.metadata.spacing_s * SAMPLES
        downsampled_count = math.floor(len(packet.data) / SAMPLES)
        downsampled_values: NDArray[np.uint8] = np.empty(downsampled_count, dtype=np.uint8)
        for i in range(downsampled_count):
            downsampled_values[i] = packet.data[i * SAMPLES]
        start_time = packet.metadata.start_sample * packet.metadata.spacing_s
        return Packet(metadata=SampleMetadata(start_time=start_time, spacing_s=downsampled_spacing_s), data=downsampled_values)

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
            values[run_index:stop_index] = packet.data * 3.3 / (1 << 8)
            run_index = stop_index
        return PlotValues(times=times, values=values)

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    to_values_lambda = Lambda(func=convert_to_values) 
    downsample_lambda = Lambda(func=downsample)
    buffer = Buffer[Packet[SampleMetadata, NDArray[np.uint8]]](max_size=100) # one second of buffer
    to_plotvalues_lambda = Lambda(func=to_plot_values)
    plotter = Plotter()

    oscilloscope.chain(to_values_lambda)
    to_values_lambda.chain(downsample_lambda)
    downsample_lambda.chain(buffer)
    buffer.chain(to_plotvalues_lambda)
    to_plotvalues_lambda.chain(plotter)
    
    oscilloscope.start()

    start_time = time.time()
    plotter.block(should_stop=lambda: time.time() - start_time > 5)

    oscilloscope.stop()

    plotter.show()
