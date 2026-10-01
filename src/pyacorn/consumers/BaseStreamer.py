from dataclasses import dataclass


DELIMITER = 0xFF
SEND_BUFFER_SIZE = 4000

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
class Packet():
    counter: int
    data: list[float]

class BaseStreamer():
    def __init__(self):
        self.buffer = bytes()

    def add(self, new_data: bytes) -> list[Packet]:
        self.buffer += new_data
        return []