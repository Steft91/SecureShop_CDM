from shared.ratelimit import TokenBucket


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_rafaga_y_recarga():
    clock = FakeClock()
    bucket = TokenBucket(rate=5, burst=10, clock=clock)
    assert all(bucket.allow() for _ in range(10))
    assert not bucket.allow()
    clock.now += 0.2  # 0.2 s × 5/s = 1 token
    assert bucket.allow()
    assert not bucket.allow()


def test_no_acumula_mas_que_la_rafaga():
    clock = FakeClock()
    bucket = TokenBucket(rate=5, burst=3, clock=clock)
    clock.now += 100
    assert [bucket.allow() for _ in range(4)] == [True, True, True, False]
