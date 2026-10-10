import time

import numpy.typing as npt
import numpy as np

from pyacorn.oscilloscopes.base import AcquisitionMode, BasicChainSettings, SampleMetadata
from pyacorn.outputs import csvwriter
from pyacorn.outputs.shared import register_stop_on_sigint
from pyacorn.chains import Lambda
from pyacorn.serial_adapter import Packet

import pyacorn.oscilloscopes.fast_pico as fast_pico

settings = BasicChainSettings(downsample_multiplier=1)

if __name__ == "__main__":
    def to_values(packet: Packet[SampleMetadata, npt.NDArray[np.float32]]) -> csvwriter.Values:
        times = np.arange(len(packet.data)) * packet.metadata.spacing_s + packet.metadata.start_time
        return csvwriter.Values(timestamped_values=np.column_stack([times, packet.data]))

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    data_packer = fast_pico.BasicChain(settings=settings)
    to_values_lambda = Lambda(func=to_values)
    csvwriter_tail = csvwriter.CSVWriter(filepath="test.txt", column_names=["Voltage"])

    oscilloscope.chain(data_packer)
    data_packer.chain(to_values_lambda)
    to_values_lambda.chain(csvwriter_tail)

    register_stop_on_sigint(oscilloscope=oscilloscope)
    oscilloscope.acquire(acquisition_mode=AcquisitionMode.multiple(5))

    while not oscilloscope.is_complete():
        time.sleep(0.1)
