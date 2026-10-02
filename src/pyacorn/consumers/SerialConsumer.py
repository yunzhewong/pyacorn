import queue
import time
from typing import Optional

import serial
import threading

class SerialConnection():
    def __init__(self, port: str):
        self.port = port

    def handle(self, abort_event: threading.Event, output_queue: queue.Queue[bytes]):
        connection = serial.Serial(port=self.port, baudrate=9600, timeout=0.1)
        while not abort_event.is_set():
            data = connection.read(8192)   # blocks until timeout or newline
            output_queue.put(data)
        connection.close()

class SerialConsumer():
    def __init__(self, port: str):
        self.output_queue = queue.Queue[bytes]()
        self._abort_event = threading.Event()
        self._connection = SerialConnection(port=port)
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._abort_event.clear()
        self._thread = threading.Thread(target=self._connection.handle, args=(self._abort_event, self.output_queue,))
        self._thread.start()

    def stop_and_join(self):
        self._abort_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None
