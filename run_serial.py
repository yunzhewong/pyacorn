import time

from pyacorn.chains.lambdas import Lambda
from pyacorn.consumers.BaseStreamer import Packet, PacketGrouper
from pyacorn.consumers.SerialConsumer import SerialConsumer

SCALE_FACTOR = 3.3 / (1 << 8)
def convert_to_voltage(packets: list[Packet]) -> list[Packet[list[float]]]:
    return [Packet(counter=packet.counter, data=[data_byte * SCALE_FACTOR for data_byte in packet.data]) for packet in packets]

if __name__ == "__main__":
    consumer = SerialConsumer(port="/dev/ttyACM0")
    consumer.start()

    packet_grouper = PacketGrouper()
    converter = Lambda(func=convert_to_voltage)

    packet_grouper.chain(converter)

    start_time = time.time()
    while time.time() - start_time < 5:
        data = consumer.output_queue.get()
        packet_grouper.add_data(data)

    consumer.stop_and_join()
    print(count / 5)
