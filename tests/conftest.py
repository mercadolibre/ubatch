import pytest

from ubatch.ubatch import UBatch


def calculate_squared_batch(xs):
    return [x ** 2 for x in xs]


@pytest.fixture
def squared_ubatch():
    squared_ubatch = UBatch(max_size=10, timeout=10)
    squared_ubatch.set_handler(handler=calculate_squared_batch)

    return squared_ubatch
