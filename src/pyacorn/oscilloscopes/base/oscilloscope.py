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


class AcquisitionCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._mode: AcquisitionMode = AcquisitionMode.continuous()
        self._counter: int = 0
        self._complete_event = threading.Event()

    def initialise(self, mode: AcquisitionMode):
        with self._lock:
            self._mode = mode
            self._counter = 0
            self._complete_event.clear()

    def increment(self):
        with self._lock:
            self._counter += 1
            if self._mode.is_complete(frame_count=self._counter):
                self.abort_acquisition()

    def wait_complete(self):
        return self._complete_event.wait()

    def abort_acquisition(self):
        self._complete_event.set()

    def is_complete(self):
        return self._complete_event.is_set()


class Oscilloscope(Head[Packet[Metadata, bytes]]):
    def __init__(self, port: str):
        super().__init__()
        self._reader = SerialPacketHandler(
            port=port,
            capture_buffer_size=CAPTURE_BUFFER_SIZE,
            on_packet=self._handle_packet,
        )
        self._rollover_count_history = RolloverCountHistory()

        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._acquisition_mode = AcquisitionMode.continuous()
        self._counter = AcquisitionCounter()

    def acquire(self, acquisition_mode: AcquisitionMode):
        self._counter.initialise(acquisition_mode)
        self._reader.start()

        def stop_handle():
            self._counter.wait_complete()
            self._reader.stop()

        self._thread = threading.Thread(target=stop_handle)
        self._thread.start()

    def stop(self):
        self._counter.abort_acquisition()
        if self._thread:
            self._thread.join()

    def is_complete(self):
        return self._counter.is_complete()

    def _handle_packet(self, packet: Packet[ByteMetadata, bytes]):
        packet_counter = self._rollover_count_history.account_for_rollover(packet.metadata.rolling_packet_counter)
        start_sample = packet_counter * CAPTURE_BUFFER_SIZE
        self.initiate(Packet(metadata=Metadata(index=start_sample), data=packet.data))
        self._counter.increment()

    def register_stop_on_sigint(self):
        signal.signal(signal.SIGINT, lambda _signum, _frame: self.stop())
