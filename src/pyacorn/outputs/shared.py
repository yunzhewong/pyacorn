import signal

from pyacorn.oscilloscopes.base import Oscilloscope


def register_stop_on_sigint(oscilloscope: Oscilloscope):
    signal.signal(signal.SIGINT, lambda _signum, _frame: oscilloscope.stop())
