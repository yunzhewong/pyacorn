import time

from pyacorn.consumers.BaseStreamer import PacketGrouper
from pyacorn.consumers.SerialConsumer import SerialConsumer


if __name__ == "__main__":
    consumer = SerialConsumer(port="/dev/ttyACM0")
    consumer.start()

    count = 0
    packet_grouper = PacketGrouper()
    start_time = time.time()
    while time.time() - start_time < 5:
        data = consumer.output_queue.get()
        count += len(data)
        output = packet_grouper.add(data)
        print([p.counter for p in output])

    consumer.stop_and_join()
    print(count / 5)
