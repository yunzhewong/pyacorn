from pyacorn.chains.StreamPacketiser import StreamPacketiserMemory


def test_pack_stream():
    memory = StreamPacketiserMemory(sample_period_s=1, running_count=2)

    packet1 = memory.pack_from_stream([5, 6, 7])
    assert packet1.running_count == 2
    assert packet1.sample_period_s == 1
    assert packet1.values == [5, 6, 7]

    packet2 = memory.pack_from_stream([1, 4])
    assert packet2.running_count == 5
    assert packet2.sample_period_s == 1
    assert packet2.values == [1, 4]
