from numpy.typing import NDArray

import numpy as np

from pyacorn.oscilloscopes.base import AcquisitionMode, BasicDataPackerSettings, SampleMetadata
from pyacorn.outputs import plotter
from pyacorn.chains.lambdas import Lambda
from pyacorn.serial_adapter import Packet

import pyacorn.oscilloscopes.fast_pico as fast_pico


settings = BasicDataPackerSettings(downsample_multiplier=1000, packets_per_update=10, plot_duration=1)

if __name__ == "__main__":
    def to_plot_values(packets: list[Packet[SampleMetadata, NDArray[np.float32]]]) -> plotter.Values:
        total_data = 0
        for packet in packets:
            total_data += len(packet.data)
        times: NDArray[np.float32] = np.zeros(total_data, dtype=np.float32) 
        values: NDArray[np.float32] = np.zeros(total_data, dtype=np.float32) 
        run_index: int = 0
        for packet in packets:
            stop_index = run_index + len(packet.data)
            times[run_index:stop_index] = np.arange(len(packet.data)) * packet.metadata.spacing_s + packet.metadata.start_time
            values[run_index:stop_index] = packet.data
            run_index = stop_index
        return plotter.Values(times=times, values=values)

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    data_packer = fast_pico.BasicDataPacker(settings=settings)
    to_plotvalues_lambda = Lambda(func=to_plot_values)
    plotter_tail = plotter.Plotter(min=fast_pico.MIN_VOLTAGE, max=fast_pico.MAX_VOLTAGE)

    oscilloscope.chain(data_packer)
    data_packer.chain(to_plotvalues_lambda)
    to_plotvalues_lambda.chain(plotter_tail)
    
    oscilloscope.acquire(acquisition_mode=AcquisitionMode.continuous())
    plotter.register_stop_on_sigint(oscilloscope=oscilloscope)

    plotter_tail.block(should_stop=oscilloscope.is_complete)
    plotter_tail.show()
