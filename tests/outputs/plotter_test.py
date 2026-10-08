from dataclasses import dataclass
import threading

import pytest

from pyacorn.outputs.plotter import Values
import numpy as np


@dataclass
class Attributes:
    _values: Values | None
    _lock: threading.Lock
    seconds_per_frame: float

    @staticmethod
    def create(frames_per_second: float):
        return Attributes(_values=None, _lock=threading.Lock(), seconds_per_frame=1 / frames_per_second)

    def change_values(self, new_values: Values):
        with self._lock:
            self._values = new_values

    def get_values(self):
        with self._lock:
            return self._values

    def calc_sleep_duration(self, elapsed_time: float):
        duration = self.seconds_per_frame - elapsed_time
        if duration > 0:
            return duration
        return 0

def test_create():
    created = Attributes.create(frames_per_second=100)
    assert created._values is None
    assert created.seconds_per_frame == 0.01

def test_change_and_get():
    created = Attributes.create(frames_per_second=100)

    new_values = Values(times=np.zeros(100), values=np.zeros(100))
    created.change_values(new_values=new_values)
    assert created._values == new_values
    assert created.get_values() == new_values 

def test_calc_sleep():
    created = Attributes.create(frames_per_second=100)

    assert created.calc_sleep_duration(0.02) == 0
    assert created.calc_sleep_duration(0.005) == pytest.approx(0.005)