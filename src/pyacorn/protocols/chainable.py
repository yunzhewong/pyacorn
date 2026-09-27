from typing import Protocol

class Upstream[T](Protocol):
    """
    Able to chain to something which outputs data
    """
    def execute(self, data: T):
        ...

class Downstream(Protocol):
    """
    Able to have other things chaining downstream from its output
    """
    def chain[T: Upstream](self, item: T) -> T:
        ...

    
