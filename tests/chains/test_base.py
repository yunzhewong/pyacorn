from pyacorn.chains.base import Body, Head, Tail
from pyacorn.protocols import chainable


def test_head():
    assert issubclass(Head, chainable.Downstream)

def test_body():
    assert issubclass(Body, chainable.Downstream)
    assert issubclass(Body, chainable.Upstream)

def test_tail():
    assert issubclass(Tail, chainable.Upstream)
    