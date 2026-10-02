from dataclasses import dataclass


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

VOLTAGE_SCALE_FACTOR = 3.3 * (1 << 8)
def to_voltage(byte: int):
    return byte * VOLTAGE_SCALE_FACTOR 

@dataclass
class Packet[T]():
    counter: int
    data: T

class PacketGrouper():
    def __init__(self):
        self.buffer = bytes()

    def add(self, new_data: bytes) -> list[Packet[bytes]]:
        self.buffer += new_data
        output = []
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
 
            data = self.buffer[:3 + CAPTURE_BUFFER_SIZE]
            self.buffer = self.buffer[3 + CAPTURE_BUFFER_SIZE:]

            packet_counter = data[1]
            data_bytes = data[2:2+CAPTURE_BUFFER_SIZE]
            crc = data[2 + CAPTURE_BUFFER_SIZE]
            if crc8(data_bytes) != crc:
                continue
            output.append(Packet(counter=packet_counter, data=data_bytes))
        return output