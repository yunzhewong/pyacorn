from pyacorn.chains.callback_map import CallbackMap


def test_callback_map():
    count1 = 0

    def func1(_: None):
        nonlocal count1
        count1 += 1

    count2 = 0

    def func2(_: None):
        nonlocal count2
        count2 += 1

    map = CallbackMap()

    func1_sub = map.add(func1)
    map.execute(None)
    assert count1 == 1
    map.add(func2)
    map.execute(None)
    assert count1 == 2
    assert count2 == 1
    map.remove(func1_sub)
    map.execute(None)
    assert count1 == 2
    assert count2 == 2
