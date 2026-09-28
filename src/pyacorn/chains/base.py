from pyacorn.protocols import chainable
import abc

from pyacorn.utils import CallbackMap

class Head[O](abc.ABC):
    def __init__(self):
        self.callback_map = CallbackMap[O]()

    def chain(self, item: chainable.Upstream[O]) -> chainable.Upstream[O]:
        self.callback_map.add(item.execute)
        return item
    
    def initiate(self, data: O):
        self.callback_map.execute(data)

class Body[I, O](abc.ABC):
    def __init__(self):
        self.callback_map = CallbackMap[O]()

    def chain(self, item: chainable.Upstream[O]) -> chainable.Upstream[O]:
        self.callback_map.add(item.execute)
        return item

    def execute(self, data: I):
        output = self.operate(data)
        self.callback_map.execute(output)

    @abc.abstractmethod
    def operate(self, data: I) -> O:
        ...

class Tail[I](abc.ABC):
    @abc.abstractmethod
    def execute(self, data: I):
        ...
