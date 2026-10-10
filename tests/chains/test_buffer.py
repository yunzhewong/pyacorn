from pyacorn.chains import Buffer
from pyacorn.chains.lambdas import Lambda


def test_batcher():
    last_value: list[str] | None = None
    count = 0

    def test(input: list[str]):
        nonlocal last_value, count
        last_value = input
        count += 1

    test_lambda = Lambda(func=test)
    buffer = Buffer(max_size=3)
    buffer.chain(test_lambda)

    buffer.execute("one")
    assert last_value == ["one"]
    assert buffer.buffered_data == ["one"]
    assert count == 1

    buffer.execute("two")
    assert last_value == ["one", "two"]
    assert buffer.buffered_data == ["one", "two"]
    assert count == 2

    buffer.execute("three")
    assert last_value == ["one", "two", "three"]
    assert buffer.buffered_data == ["one", "two", "three"]
    assert count == 3

    buffer.execute("four")
    assert last_value == ["two", "three", "four"]
    assert buffer.buffered_data == ["two", "three", "four"]
    assert count == 4

    buffer.execute("five")
    assert last_value == ["three", "four", "five"]
    assert buffer.buffered_data == ["three", "four", "five"]
    assert count == 5
