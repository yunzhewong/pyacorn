from dataclasses import dataclass

from pyacorn.chains.base import Head
from pyacorn.serial_adapter import ByteMetadata, Packet, RolloverCountHistory, SerialPacketHandler

CAPTURE_BUFFER_SIZE = 2000 
BYTES_PER_FLOAT = 1
SPACING_S = 1 / 500_000
SCALE_FACTOR = 3.3 / (1 << 8)

_DTYPES = {1: "<u1", 2: "<u2", 4: "<u4", 8: "<u8"}  # little-endian, unsigned
DTYPE = _DTYPES[BYTES_PER_FLOAT]
VALS_PER_PACKET = int(CAPTURE_BUFFER_SIZE / BYTES_PER_FLOAT)

@dataclass
class Metadata:
    start_sample: int

class Oscilloscope(Head[Packet[Metadata, bytes]]):
    def __init__(self, port: str):
        super().__init__()
        self.reader = SerialPacketHandler(port=port, capture_buffer_size=CAPTURE_BUFFER_SIZE, on_packet=self._handle_packet)
        self.rollover_count_history = RolloverCountHistory()

    def start(self):
        self.reader.start()

    def stop(self):
        self.reader.stop()

    def _handle_packet(self, packet: Packet[ByteMetadata, bytes]):
        packet_counter = self.rollover_count_history.account_for_rollover(packet.metadata.rolling_packet_counter)
        start_sample = packet_counter * CAPTURE_BUFFER_SIZE
        self.initiate(Packet(metadata=Metadata(start_sample=start_sample), data=packet.data))