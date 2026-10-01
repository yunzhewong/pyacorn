from typing import Protocol, runtime_checkable

@runtime_checkable
class Upstream[T](Protocol):
    """
    Able to chain to something which outputs data
    """
    def execute(self, data: T):
        ...

    def get_input_type(self) -> type:
        ...


@runtime_checkable
class Downstream(Protocol):
    """
    Able to have other things chaining downstream from its output
    """
    def chain[T: Upstream](self, item: T) -> T:
        ...

    def get_output_type(self) -> type:
        ...
