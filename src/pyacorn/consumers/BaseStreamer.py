from dataclasses import dataclass

from pyacorn.chains.base import Body, Head


DELIMITER = 0xFF
CAPTURE_BUFFER_SIZE = 2000

def crc8(data: bytes, init: int = 0xFF, poly: int = 0x07) -> int:
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

# _TABLE = []
# for i in range(256):
#     c = i
#     for _ in range(8):
#         c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
#     _TABLE.append(c)

# def crc8_fast(data: bytes, init: int = 0xFF) -> int:
#     crc = init
#     for byte in data:
#         crc = _TABLE[crc ^ byte]
#     return crc

@dataclass
class ByteMetadata():
    packet_counter: int

@dataclass
class Packet[M, T]():
    metadata: M
    data: T

class SerialBuffer(Head[list[Packet[ByteMetadata, bytes]]]):
    def __init__(self):
        super().__init__()
        self.buffer = bytes()

    def handle_new_data(self, new_data: bytes):
        self.buffer += new_data
        output: list[Packet[ByteMetadata, bytes]] = []
        while len(self.buffer) >= 3 + CAPTURE_BUFFER_SIZE:
            skip = 0
            while self.buffer[skip] != DELIMITER and skip < len(self.buffer):
                skip += 1

            if skip > len(self.buffer):
                self.buffer = bytes()
                break

            self.buffer = self.buffer[skip:]
            if len(self.buffer) < 3 + CAPTURE_BUFFER_SIZE:
                break
 
            buffer_bytes = self.buffer[:3 + CAPTURE_BUFFER_SIZE]
            self.buffer = self.buffer[3 + CAPTURE_BUFFER_SIZE:]

            packet_counter = buffer_bytes[1]
            data_bytes = buffer_bytes[2:2+CAPTURE_BUFFER_SIZE]
            crc = buffer_bytes[2 + CAPTURE_BUFFER_SIZE]
            if crc8(data_bytes) != crc:
                continue
            output.append(Packet(metadata=ByteMetadata(counter=packet_counter), data=data_bytes))
        return output