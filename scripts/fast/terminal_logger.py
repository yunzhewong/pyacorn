import numpy as np
import numpy.typing as npt

import pyacorn.oscilloscopes.fast_pico as fast_pico
from pyacorn.chains import Lambda
from pyacorn.oscilloscopes.base import (
    AcquisitionMode,
    BasicChainSettings,
    SampleMetadata,
)
from pyacorn.oscilloscopes.serial_adapter import Packet
from pyacorn.outputs import terminal_logger
from pyacorn.outputs.shared import register_stop_on_sigint

settings = BasicChainSettings(downsample_multiplier=100)

if __name__ == "__main__":

    def to_values(
        packet: Packet[SampleMetadata, npt.NDArray[np.float32]],
    ) -> terminal_logger.Values:
        time_centre = (
            packet.metadata.start_time
            + ((len(packet.data) - 1) / 2) * packet.metadata.spacing_s
        )
        average_value = np.mean(packet.data)
        return terminal_logger.Values(time=time_centre, text=f"{(average_value):.2f}")

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    data_packer = fast_pico.BasicChain(settings=settings)
    to_values_lambda = Lambda(func=to_values)
    output = terminal_logger.TerminalLogger()

    oscilloscope.chain(data_packer)
    data_packer.chain(to_values_lambda)
    to_values_lambda.chain(output)

    register_stop_on_sigint(oscilloscope=oscilloscope)
    oscilloscope.acquire(acquisition_mode=AcquisitionMode.continuous())
