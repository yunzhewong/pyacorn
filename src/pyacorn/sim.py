from dataclasses import dataclass
import math
import threading
import time
from typing import Callable, Optional

from pyacorn.chains.base import Head

def should_output(last_time: float, current_time: float, output_period_s: float):
    return current_time - last_time > output_period_s

def calc_output_pause(output_period_s: float):
    return output_period_s / 2 # time.sleep can run a bit long, so check twice as frequently

def calc_elapsed_readings(start_time: float, end_time: float, sample_period_s: float) -> int:
    return math.floor((end_time - start_time) / sample_period_s)

def generate_timed_array[T](func: Callable[[float], T], start_time: float, number_of_readings: int, sample_period_s: float) -> list[T]:
    values: list[T] = []
    for i in range(number_of_readings):
        reading_time = start_time + i * sample_period_s
        reading_value = func(reading_time)
        values.append(reading_value)
    return values

@dataclass
class Parameters[T]():
    func: Callable[[float], T]
    sample_period_s: float
    output_period_s: float

    def execute(self, last_time: float, current_time: float) -> tuple[float, list[T]]:
        elapsed_readings = calc_elapsed_readings(start_time=last_time, end_time=current_time, sample_period_s=self.sample_period_s)
        values = generate_timed_array(func=self.func, start_time=last_time, number_of_readings=elapsed_readings, sample_period_s=self.sample_period_s)
        return last_time + elapsed_readings * self.sample_period_s, values 

class Stream[T](Head[list[T]]):
    def __init__(self, func: Callable[[float], T], sample_period_s: float, output_period_s: float):
        super().__init__()
        self.params = Parameters(func=func, sample_period_s=sample_period_s, output_period_s=output_period_s)
        self._abort_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
    def _handle(self):
        output_time = time.time()
        while not self._abort_event.is_set():
            loop_time = time.time()
            if not should_output(last_time=output_time, current_time=loop_time, output_period_s=self.params.output_period_s):
                time.sleep(calc_output_pause(self.params.output_period_s / 2))
                continue
            output_time, values = self.params.execute(last_time=output_time, current_time=loop_time)
            self.callback_map.execute(values)

    def start(self):
        self._abort_event.clear()
        self._thread = threading.Thread(target=self._handle)
        self._thread.start()

    def stop_and_join(self):
        self._abort_event.set()
        if self._thread is not None:
            self._thread.join()

