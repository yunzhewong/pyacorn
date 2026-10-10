import numpy as np
import pytest

from pyacorn.outputs.plotter import Attributes, Values


def test_create():
    created = Attributes(frames_per_second=100)
    assert created._values is None
    assert created.seconds_per_frame == 0.01


def test_change_and_get():
    created = Attributes(frames_per_second=100)
    new_values = Values(times=np.zeros(100, dtype=np.float32), values=np.zeros(100, dtype=np.float32))
    created.change_values(new_values=new_values)
    assert created._values == new_values
    assert created.get_values() == new_values


def test_calc_sleep():
    created = Attributes(frames_per_second=100)
    assert created.calc_sleep_duration(0.02) == 0
    assert created.calc_sleep_duration(0.005) == pytest.approx(0.005)
