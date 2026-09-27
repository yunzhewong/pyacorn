from typing import Protocol

class UpstreamChainable[T](Protocol):
    """
    Able to chain to something which outputs data
    """
    def execute(self, data: T):
        ...

class DownstreamChainable(Protocol):
    """
    Able to have other things chaining downstream from its output
    """
    def chain[T: UpstreamChainable](self, item: T) -> T:
        ...

    
