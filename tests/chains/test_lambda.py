from pyacorn.chains import Lambda


def test_lambda():
    outputs: list[str] = []

    def func(s: str):
        outputs.append(s)

    new_lambda = Lambda(func)

    new_lambda.execute("hello")
    assert outputs == ["hello"]

    new_lambda.execute("goodbye")
    assert outputs == ["hello", "goodbye"]
