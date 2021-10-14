import pytest

from ubatch.data_request import _DataRequest, _DataRequestBuffer, DataRequestBufferFull


def test_data_request_buffer_contains_true():
    data_buffer = _DataRequestBuffer(size=10)
    data_request = _DataRequest(timeout=10)

    data_buffer.append(data_request)

    assert data_request in data_buffer


def test_data_request_buffer_contains_false():
    data_buffer = _DataRequestBuffer(size=10)
    data_request = _DataRequest(timeout=10)

    assert data_request not in data_buffer


def test_full_data_request_buffer_raises_buffer_full():
    data_buffer = _DataRequestBuffer(size=1)

    with pytest.raises(DataRequestBufferFull):
        for i in range(2):
            data_buffer.append(_DataRequest(timeout=10))


def test_data_request_buffer_iterate_over_all_items():
    data_buffer = _DataRequestBuffer(size=10)

    data_buffer.append(_DataRequest(timeout=10))
    data_buffer.append(_DataRequest(timeout=10))

    for i in data_buffer:
        assert isinstance(i, _DataRequest)


def test_data_request_buffer_len_on_items():
    data_buffer = _DataRequestBuffer(size=10)

    data_buffer.append(_DataRequest(timeout=10))

    assert len(data_buffer) == 1


def test_data_request_buffer_len_when_empty():
    data_buffer = _DataRequestBuffer(size=10)

    assert len(data_buffer) == 0


def test_data_request_buffer_time_is_over_false_on_empty_buffer():
    data_buffer = _DataRequestBuffer(size=10)
    assert data_buffer.time_is_over() is False


@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_data_request_buffer_time_is_over_true_if_any(freezer):
    data_buffer = _DataRequestBuffer(size=10)

    data_request1 = _DataRequest(timeout=5)
    data_request2 = _DataRequest(timeout=10)

    data_buffer.append(data_request1)
    data_buffer.append(data_request2)

    freezer.move_to("2018-09-07 16:35:06.000")

    assert data_request1.time_is_over() is True
    assert data_request2.time_is_over() is False

    assert data_buffer.time_is_over() is True


@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_data_request_buffer_time_is_over_in_future_if_any(freezer):
    data_buffer = _DataRequestBuffer(size=10)

    data_request1 = _DataRequest(timeout=5)
    data_request2 = _DataRequest(timeout=10)

    data_buffer.append(data_request1)
    data_buffer.append(data_request2)

    freezer.move_to("2018-09-07 16:35:03.000")

    assert data_request1.time_is_over() is False
    assert data_request2.time_is_over() is False

    assert data_buffer.time_is_over(future=2) is True


def test_data_request_buffer_full_true_if_full():
    data_buffer = _DataRequestBuffer(size=2)

    for _ in range(2):
        data_buffer.append(_DataRequest(timeout=5))

    assert data_buffer.full() is True


def test_data_request_buffer_full_false_if_not_full():
    data_buffer = _DataRequestBuffer(size=2)

    data_buffer.append(_DataRequest(timeout=5))

    assert data_buffer.full() is False


def test_data_request_buffer_space_left_when_not_elements():
    data_buffer = _DataRequestBuffer(size=10)
    assert data_buffer.space_left() == 10


def test_data_request_buffer_space_left_decrease_on_elements():
    data_buffer = _DataRequestBuffer(size=10)
    data_buffer.append(_DataRequest(timeout=5))
    assert data_buffer.space_left() == 9


def test_data_request_buffer_clear_remove_all_elements():
    data_buffer = _DataRequestBuffer(size=10)
    data_buffer.append(_DataRequest(timeout=5))
    data_buffer.clear()
    assert len(data_buffer) == 0


def test_data_request_buffer_get_input_args():
    data_buffer = _DataRequestBuffer(size=10)
    data_buffer.append(_DataRequest(timeout=5, args=(1, 2)))
    data_buffer.append(_DataRequest(timeout=5, args=(7, 5)))

    assert data_buffer.get_input_args() == [[1, 7], [2, 5]]


def test_data_request_buffer_get_input_kwargs():
    data_buffer = _DataRequestBuffer(size=10)
    data_buffer.append(_DataRequest(timeout=5, kwargs={'par': 'foo'}))
    data_buffer.append(_DataRequest(timeout=5, kwargs={'par': 'bar'}))

    assert data_buffer.get_input_kwargs() == {'par': ['foo', 'bar']}


def test_data_request_buffer_set_outputs_store_outputs_in_order():
    data_buffer = _DataRequestBuffer(size=10)
    data1 = _DataRequest(args=("foo", ), timeout=5)
    data2 = _DataRequest(args=("bar", ), timeout=5)
    data_buffer.append(data1)
    data_buffer.append(data2)

    data_buffer.set_outputs(["foo_output", "bar_output"])

    assert data1.output == "foo_output"
    assert data2.output == "bar_output"


def test_data_request_buffer_set_exception_store_exception_in_all():
    data_buffer = _DataRequestBuffer(size=10)
    data1 = _DataRequest(args=("foo", ), timeout=5)
    data2 = _DataRequest(args=("bar", ), timeout=5)
    data_buffer.append(data1)
    data_buffer.append(data2)

    data_buffer.set_exception(ValueError)

    assert data1.exception == data2.exception == ValueError
