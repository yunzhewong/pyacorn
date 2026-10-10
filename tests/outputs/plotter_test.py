import numpy as np
import pytest

from pyacorn.oscilloscopes.base import BasicChainSettings
from pyacorn.outputs.plotter import Attributes, Values, calculate_buffer_size


def test_calculate_buffer_size():
    assert calculate_buffer_size(BasicChainSettings(downsample_multiplier=1, frame_rate=60), plot_duration_s=1) == 60
    assert calculate_buffer_size(BasicChainSettings(downsample_multiplier=50, frame_rate=30), plot_duration_s=10) == 300


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
