import numpy as np
import numpy.typing as npt

import pyacorn.oscilloscopes.fast_pico as fast_pico
from pyacorn.chains import Lambda
from pyacorn.oscilloscopes.base.serial_adapter import Packet
from pyacorn.oscilloscopes.base.structs import (
    AcquisitionMode,
    BasicChainSettings,
    SampleMetadata,
)
from pyacorn.outputs import csvwriter

settings = BasicChainSettings(downsample_multiplier=1)

if __name__ == "__main__":

    def to_values(
        packet: Packet[SampleMetadata, npt.NDArray[np.float32]],
    ) -> csvwriter.Values:
        times = np.arange(len(packet.data)) * packet.metadata.spacing_s + packet.metadata.start_time
        return csvwriter.Values(timestamped_values=np.column_stack([times, packet.data]))

    oscilloscope = fast_pico.Oscilloscope(port="/dev/ttyACM0")
    data_packer = fast_pico.BasicChain(settings=settings)
    to_values_lambda = Lambda(func=to_values)
    output = csvwriter.CSVWriter(filepath="test.txt", column_names=["Voltage (V)"])

    oscilloscope.chain(data_packer)
    data_packer.chain(to_values_lambda)
    to_values_lambda.chain(output)

    oscilloscope.register_stop_on_sigint()
    oscilloscope.acquire(
        acquisition_mode=AcquisitionMode.until_frames_captured(
            min_frames=int(500_000 / 2000),
            settings=settings,
            parameters=fast_pico.PARAMETERS,
        )
    )
