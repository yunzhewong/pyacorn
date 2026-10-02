import queue
import time
from typing import Optional

import serial
import threading

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
