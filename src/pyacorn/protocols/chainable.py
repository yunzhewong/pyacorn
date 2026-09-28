from typing import Protocol, runtime_checkable

@runtime_checkable
class Upstream[T](Protocol):
    """
    Able to chain to something which outputs data
    """
    def execute(self, data: T):
        ...

@runtime_checkable
class Downstream(Protocol):
    """
    Able to have other things chaining downstream from its output
    """
    def chain[T: Upstream](self, item: T) -> T:
        ...

    
