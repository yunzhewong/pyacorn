import copy
import threading
from typing import Optional, override

from pyacorn.chains.base import Body


class Decoupler[T](Body[T, T]):
    def __init__(self, period_s: float):
        super().__init__()
        self.lock = threading.Lock()
        self.value: Optional[T] = None  
        self.timer = threading.Timer(interval=period_s, function=self._on_periodic)
        self.timer.start()

    @override
    def execute(self, data: T):
        with self.lock:
            self.value = data
            print(self.value)
    def _on_periodic(self):
        print("called")
        with self.lock:
            print(self.value)
        #     if self.value is None:
        #         return
        #     value_copy = copy.deepcopy(self.value)
        # self.callback_map.execute(value_copy)

    def operate(self, data: T) -> T:
        raise NotImplementedError()