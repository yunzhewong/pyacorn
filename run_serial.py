import time

from pyacorn.consumers.BaseStreamer import BaseStreamer
from pyacorn.consumers.SerialConsumer import SerialConsumer


if __name__ == "__main__":
    consumer = SerialConsumer(port="/dev/ttyACM0")
    consumer.start()

    base_streamer = BaseStreamer()
    start_time = time.time()
    while time.time() - start_time < 5:
        data = consumer.output_queue.get()
        output = base_streamer.add(data)

    consumer.stop_and_join()
