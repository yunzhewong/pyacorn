import time

from pyacorn.consumers.SerialConsumer import SerialConsumer


if __name__ == "__main__":
    consumer = SerialConsumer(port="/dev/ttyACM0")
    consumer.start()

    count = 0
    start_time = time.time()
    while time.time() - start_time < 5:
        data = consumer.output_queue.get()
        count += len(data)
        print(len(data))

    consumer.stop_and_join()

    print(count)

    bytes_per_second = count / 5 
    print(f"Bytes per second: {bytes_per_second}")