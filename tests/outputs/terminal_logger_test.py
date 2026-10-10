from pyacorn.outputs.terminal_logger import Values


def test_values():
    assert Values(time=15, text="Hello").to_log_data() == "(15.00) Hello"
    assert Values(time=12.555, text="Goodbye").to_log_data() == "(12.55) Goodbye"
