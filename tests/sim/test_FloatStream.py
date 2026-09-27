import pytest

from pyacorn.sim.FloatStream import Parameters, calc_output_pause, should_output, calc_elapsed_readings, generate_float_array
from pyacorn.utils import CallbackMap

def test_should_output():
    assert should_output(last_time=0, current_time=1, output_period_s=0.5)
    assert not should_output(last_time=0, current_time=0.4, output_period_s=0.5)
    assert not should_output(0, 2, output_period_s=2)
    assert should_output(4, 6, output_period_s=1.5)

def test_calc_output_pause():
    assert calc_output_pause(1) == 0.5
    assert calc_output_pause(0.02) == 0.01

def test_calc_elapsed_readings():
    assert calc_elapsed_readings(0, 1, sample_period_s=0.1) == 10
    assert calc_elapsed_readings(0, 1.09, sample_period_s=0.1) == 10
    assert calc_elapsed_readings(0, 0.01, sample_period_s=0.1) == 0
    assert calc_elapsed_readings(0, 5, sample_period_s=0.25) == 20

def test_generation():
    def func(val: float):
        return val

    values = generate_float_array(func=func, start_time=0, number_of_readings=10, sample_period_s=0.1)

    assert values == pytest.approx([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])

def test_sim_stream_execute():
    def func(t: float):
        return t

    outputs: list[list[float]] = []
    def append_outputs(data: list[float]):
        outputs.append(data)

    callback_map = CallbackMap()
    callback_map.add(append_outputs)

    params = Parameters(func=func, sample_period_s=0.1, output_period_s=1, callback_map=callback_map)

    new_time = params.execute(0, 1)
    assert new_time == 1
    assert len(outputs) == 1
    assert outputs[0] == pytest.approx([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])

    new_time = params.execute(1, 1.95)
    assert new_time == 1.9
    assert len(outputs) == 2
    assert outputs[1] == pytest.approx([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8])

    new_time = params.execute(1.9, 2.5)
    assert new_time == 2.5
    assert len(outputs) == 3
    assert outputs[2] == pytest.approx([1.9, 2, 2.1, 2.2, 2.3, 2.4])
