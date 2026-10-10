from pyacorn.chains import Batcher
from pyacorn.chains.lambdas import Lambda


def test_batcher():
    outputs: list[list[str]] = []

    def test(input: list[str]):
        outputs.append(input)

    test_lambda = Lambda(func=test)
    batcher = Batcher(batch_size=4)
    batcher.chain(test_lambda)

    batcher.execute("one")
    assert len(outputs) == 0
    assert len(batcher.buffer) == 1
    batcher.execute("two")
    assert len(outputs) == 0
    assert len(batcher.buffer) == 2
    batcher.execute("three")
    assert len(outputs) == 0
    assert len(batcher.buffer) == 3
    batcher.execute("four")
    assert len(outputs) == 1
    assert len(batcher.buffer) == 0
    assert outputs[0] == ["one", "two", "three", "four"]
