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

def to_voltage(byte: int):
    return 3.3 * (byte / (1 << 8)) 

@dataclass
class Packet():
    counter: int
    values: list[float]

class BaseStreamer():
    def __init__(self):
        self.buffer = bytes()

    def add(self, new_data: bytes) -> list[Packet]:
        self.buffer += new_data
        output = []
        while len(self.buffer) >= 3 + CAPTURE_BUFFER_SIZE:
            skip = 0
            while self.buffer[skip] != DELIMITER:
                skip += 1
            if len(self.buffer) - skip < 3 + CAPTURE_BUFFER_SIZE:
                self.buffer = self.buffer[skip:]
                break
            data = self.buffer[skip: skip + 3 + CAPTURE_BUFFER_SIZE]
            self.buffer = self.buffer[skip + 3 + CAPTURE_BUFFER_SIZE:]

            if crc8(data[2:2 + CAPTURE_BUFFER_SIZE]) != data[2 + CAPTURE_BUFFER_SIZE]:
                continue
            data_bytes = data[2:2+CAPTURE_BUFFER_SIZE]
            values = [to_voltage(byte) for byte in data_bytes]
            output.append(Packet(counter=data[1], values=values))
        print(output)
        return output