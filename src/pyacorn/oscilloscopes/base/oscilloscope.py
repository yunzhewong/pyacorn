import signal
import threading

from pyacorn.chains.base import Head
from pyacorn.oscilloscopes.base.structs import CAPTURE_BUFFER_SIZE, AcquisitionMode, Metadata

from .serial_adapter import (
    ByteMetadata,
    Packet,
    RolloverCountHistory,
    SerialPacketHandler,
)


class Oscilloscope(Head[Packet[Metadata, bytes]]):
    def __init__(self, port: str):
        super().__init__()
        self._reader = SerialPacketHandler(
            port=port,
            capture_buffer_size=CAPTURE_BUFFER_SIZE,
            on_packet=self._handle_packet,
        )
        self._rollover_count_history = RolloverCountHistory()

        self._complete_event = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._acquisition_mode = AcquisitionMode.continuous()
        self._counter: int = 0

    def acquire(self, acquisition_mode: AcquisitionMode):
        with self._lock:
            self._acquisition_mode = acquisition_mode
            self._counter = 0
        self._complete_event.clear()
        self._reader.start()

        def stop_handle():
            self._complete_event.wait()
            self._reader.stop()

        self._thread = threading.Thread(target=stop_handle)
        self._thread.start()

    def stop(self):
        self._complete_event.set()
        if self._thread:
            self._thread.join()

    def is_complete(self):
        return self._complete_event.is_set()

    def _handle_packet(self, packet: Packet[ByteMetadata, bytes]):
        packet_counter = self._rollover_count_history.account_for_rollover(packet.metadata.rolling_packet_counter)
        start_sample = packet_counter * CAPTURE_BUFFER_SIZE
        self.initiate(Packet(metadata=Metadata(start_sample=start_sample), data=packet.data))
        with self._lock:
            self._counter += 1
            if self._acquisition_mode.is_complete(frame_count=self._counter):
                self._complete_event.set()

    def register_stop_on_sigint(self):
        signal.signal(signal.SIGINT, lambda _signum, _frame: self.stop())
