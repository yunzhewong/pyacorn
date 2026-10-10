from pyacorn.outputs.csvwriter import write_header


def test_write_header():
    assert write_header(["Voltage (V)"]) == "Time (s), Voltage (V)\n"
    assert write_header(["Voltage 1 (V)", "Voltage 2 (V)"]) == "Time (s), Voltage 1 (V), Voltage 2 (V)\n"
