import time

import numpy.typing as npt
import numpy as np

from pyacorn.oscilloscopes.base import AcquisitionMode, BasicDataPackerSettings, SampleMetadata
from pyacorn.outputs import terminal_logger
from pyacorn.outputs.shared import register_stop_on_sigint
from pyacorn.chains import Lambda
from pyacorn.serial_adapter import Packet

import pyacorn.oscilloscopes.fast_pico as fast_pico

settings = BasicDataPackerSettings(downsample_multiplier=100, packets_per_update=10)

if __name__ == "__main__":
    def to_values(packets: list[Packet[SampleMetadata, npt.NDArray[np.float32]]]) -> terminal_logger.Values:
        time_sum = 0
        value_sum = 0

        for packet in packets:
            packet_length = len(packet.data)
            time_centre = packet.metadata.start_time + ((packet_length - 1)/ 2) * packet.metadata.spacing_s 
            time_sum += time_centre
            value_sum += np.mean(packet.data)
        
        return terminal_logger.Values(time=time_sum / len(packets), text=f"{(value_sum / len(packets)):.2f}")

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    data_packer = fast_pico.BasicDataPacker(settings=settings)
    to_values_lambda = Lambda(func=to_values)
    terminal_logger_tail = terminal_logger.TerminalLogger()

    oscilloscope.chain(data_packer)
    data_packer.chain(to_values_lambda)
    to_values_lambda.chain(terminal_logger_tail)

    register_stop_on_sigint(oscilloscope=oscilloscope)
    oscilloscope.acquire(acquisition_mode=AcquisitionMode.continuous())

    while not oscilloscope.is_complete():
        time.sleep(0.1)
