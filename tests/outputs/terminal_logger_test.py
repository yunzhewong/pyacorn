from pyacorn.outputs.terminal_logger import Values


def test_values():
    assert Values(time=15, text="12.25").to_log_data() == "(15.00) 12.25"
    assert Values(time=12.555, text="1.08").to_log_data() == "(12.55) 1.08"
