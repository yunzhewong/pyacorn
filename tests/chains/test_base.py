from pyacorn.chains.base import Body, Head, Tail
from pyacorn.chains import protocol as chainable


def test_head_protocols():
    assert issubclass(Head, chainable.Downstream)

def test_body_protocols():
    assert issubclass(Body, chainable.Downstream)
    assert issubclass(Body, chainable.Upstream)

def test_tail_protocols():
    assert issubclass(Tail, chainable.Upstream)
    