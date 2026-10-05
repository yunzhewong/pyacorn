from dataclasses import dataclass

from pyacorn.chains.base import Head
from pyacorn.serial_adapter import ByteMetadata, Packet, RolloverCountHistory, SerialPacketReader

FAST_PICO_CAPTURE_BUFFER_SIZE = 2000 
FAST_PICO_BYTES_PER_FLOAT = 1
FAST_PICO_SPACING_S = 1 / 500_000
FAST_PICO_SCALE_FACTOR = 3.3 / (1 << 8)

@dataclass
class FastPicoMetadata:
    start_sample: int
    bytes_per_float: int = FAST_PICO_BYTES_PER_FLOAT
    spacing_s: float = FAST_PICO_SPACING_S
    scale_factor: float = FAST_PICO_SCALE_FACTOR


class FastPicoOscilloscope(Head[Packet[FastPicoMetadata, bytes]]):
    def __init__(self, port: str):
        super().__init__()
        self.reader = SerialPacketReader(port=port, capture_buffer_size=FAST_PICO_CAPTURE_BUFFER_SIZE, on_packet=self._handle_packet)
        self.rollover_count_history = RolloverCountHistory()

    def start(self):
        self.reader.start()

    def stop(self):
        self.reader.stop()

    def _handle_packet(self, packet: Packet[ByteMetadata, bytes]):
        packet_counter = self.rollover_count_history.account_for_rollover(packet.metadata.rolling_packet_counter)
        start_sample = packet_counter * FAST_PICO_CAPTURE_BUFFER_SIZE
        self.initiate(Packet(metadata=FastPicoMetadata(start_sample=start_sample), data=packet.data))