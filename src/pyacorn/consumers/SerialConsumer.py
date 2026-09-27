import time
from typing import Callable, Optional

import serial
import threading

from pyacorn.utils import CallbackMap

class SerialConnection():
    def __init__(self, port: str, callback_map: CallbackMap[bytes]):
        self.port = port
        self.callback_map = callback_map
        self.abort_event = threading.Event()

    def handle(self):
        connection = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
        while not self.abort_event.is_set():
            data = connection.read(8192)   # blocks until timeout or newline
            self.callback_map.execute(data)
        connection.close()

    def abort(self):
        self.abort_event.set()

    def clear(self):
        self.abort_event.clear()

    def start(self):
        self.abort_event.clear()
        self._thread = threading.Thread(target=self.handle)
        self._thread.start()
        
    def stop(self):
        self.abort_event.set()
        if self._thread is not None:
            self._thread.join()

class SerialConsumer():
    def __init__(self, port: str, on_data: Callable[[bytes], None]):
        callback_map = CallbackMap[bytes]()
        self.callback_id = callback_map.add(on_data)
        self.connection = SerialConnection(port=port, callback_map=callback_map)
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.connection.clear()
        self.thread = threading.Thread(target=self.connection.handle)
        self.thread.start()

    def stop_and_join(self):
        self.connection.abort()
        if self.thread:
            self.thread.join()
            self.thread = None

if __name__ == "__main__":
    count = 0
    prev_time = time.time()
    times: list[float] = []
    def callback(bytes: bytes):
        global count, prev_time
        count += len(bytes)
        current_time = time.time()
        times.append(current_time - prev_time)
        prev_time = current_time

    consumer = SerialConsumer(port="/dev/ttyACM0", on_data=callback)
    consumer.start()

    time.sleep(5)
    consumer.stop_and_join()

    print(count)

    bytes_per_second = count / 5 
    print(f"Bytes per second: {bytes_per_second}")
    print(sum(times) / len(times))