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


DOWNSAMPLE_INTERVAL = 1000
BATCHER_SIZE = 10
VIEWING_SIZE_S = 10

BUFFER_SIZE = int(fast_pico.SAMPLES_PER_SECOND / DOWNSAMPLE_INTERVAL * VIEWING_SIZE_S)


@dataclass
class SampleMetadata:
    start_time: float
    spacing_s: float

if __name__ == "__main__":
    def to_data_packet(packets: list[Packet[fast_pico.Metadata, bytes]]) -> Packet[SampleMetadata, NDArray[np.uint8]]:
        total_values = 0
        for packet in packets:
            total_values += len(packet.data)

        start_time = packets[0].metadata.start_sample * fast_pico.SPACING_S
        spacing_s = fast_pico.SPACING_S * DOWNSAMPLE_INTERVAL
        downsampled_count = math.floor(total_values / DOWNSAMPLE_INTERVAL)
        values = np.zeros(downsampled_count, dtype=np.uint8)

        value_index = 0
        running_index = 0
        for packet in packets:
            packet_values = np.frombuffer(packet.data, dtype=fast_pico.DTYPE, count=fast_pico.VALS_PER_PACKET)
            while running_index < len(packet_values):
                values[value_index] = packet_values[running_index]
                value_index += 1
                running_index += DOWNSAMPLE_INTERVAL            
            running_index -= len(packet_values)

        return Packet(metadata=SampleMetadata(start_time=start_time, spacing_s=spacing_s), data=values)

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
    batcher = Batcher(batch_size=BATCHER_SIZE)
    to_data_lambda = Lambda(func=to_data_packet) 
    buffer = Buffer[Packet[SampleMetadata, NDArray[np.uint8]]](max_size=BUFFER_SIZE)
    to_plotvalues_lambda = Lambda(func=to_plot_values)
    plotter = Plotter()

    oscilloscope.chain(batcher)
    batcher.chain(to_data_lambda)
    to_data_lambda.chain(buffer)
    buffer.chain(to_plotvalues_lambda)
    to_plotvalues_lambda.chain(plotter)
    
    oscilloscope.start()

    start_time = time.time()
    plotter.block(should_stop=lambda: time.time() - start_time > 20)

    oscilloscope.stop()

    plotter.show()
