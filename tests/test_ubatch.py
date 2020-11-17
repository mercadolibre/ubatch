import pytest

from queue import Empty

from ubatch.data_request import DataRequest, DataRequestBuffer
from ubatch.ubatch import HandlerNotSet, BadBatchOutputSize


def in_batch(input_data):
    return [x ** 2 for x in input_data]


@pytest.mark.timeout(1)
def test_ubatch_ubatch_return_datarequest_output(mocker, squared_ubatch):
    mocker.patch("time.sleep")

    mocker.patch(
        "ubatch.ubatch.DataRequest.ready", new_callable=mocker.PropertyMock
    ).return_value = True

    mocker.patch(
        "ubatch.ubatch.DataRequest.output", new_callable=mocker.PropertyMock
    ).return_value = "foo"

    assert squared_ubatch.ubatch("bar") == "foo"


@pytest.mark.timeout(1)
def test_ubatch_put_enqueue_data_request(mocker, squared_ubatch):
    mocker.patch("ubatch.ubatch.DataRequest")

    mocked_queue = mocker.patch.object(squared_ubatch._requests_queue, "put")

    squared_ubatch.ubatch("bar")

    mocked_queue.assert_called_once()


@pytest.mark.timeout(1)
def test_ubatch_procces_in_batch_set_outputs(mocker, squared_ubatch):
    buffer = DataRequestBuffer(size=5)
    data1 = DataRequest(data=2, timeout=5)
    data2 = DataRequest(data=3, timeout=5)

    buffer.append(data1)
    buffer.append(data2)

    mocked_wait = mocker.patch.object(squared_ubatch, "_wait_buffer_ready")
    mocked_wait.return_value = buffer

    squared_ubatch._procces_in_batch()

    assert data1.output == 4
    assert data2.output == 9


@pytest.mark.timeout(1)
def test_ubatch_procces_in_batch_set_exceptions(mocker, squared_ubatch):
    buffer = DataRequestBuffer(size=5)
    data1 = DataRequest(data=2, timeout=5)
    data2 = DataRequest(data=3, timeout=5)

    buffer.append(data1)
    buffer.append(data2)

    squared_ubatch._handler = mocker.Mock(side_effect=ValueError)

    mocked_wait = mocker.patch.object(squared_ubatch, "_wait_buffer_ready")
    mocked_wait.return_value = buffer

    squared_ubatch._procces_in_batch()

    with pytest.raises(ValueError):
        data1.output

    with pytest.raises(ValueError):
        data2.output


@pytest.mark.timeout(1)
@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_ubatch_wait_ready_buffer_break_when_buffer_full(mocker, squared_ubatch):
    for i in range(10):
        squared_ubatch._requests_queue.put(DataRequest(data=i, timeout=5))

    buffer = squared_ubatch._wait_buffer_ready()

    with pytest.raises(Empty):
        squared_ubatch._requests_queue.get(block=False)

    assert len(buffer) == 10


@pytest.mark.timeout(1)
@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_ubatch_wait_ready_buffer_break_when_buffer_timeout(
    mocker, freezer, squared_ubatch
):
    data1 = DataRequest(data=2, timeout=5)  # time over
    data2 = DataRequest(data=2, timeout=10)  # no time over

    freezer.move_to("2018-09-07 16:35:06.000")
    assert data1.time_is_over() is True
    assert data2.time_is_over() is False

    squared_ubatch._requests_queue.put(data1)
    squared_ubatch._requests_queue.put(data2)

    buffer = squared_ubatch._wait_buffer_ready()

    with pytest.raises(Empty):
        squared_ubatch._requests_queue.get(block=False)

    assert buffer._buffer == [data1, data2]


def test_procces_in_batch_raise_bad_batch_output_size(mocker, squared_ubatch):
    data1 = DataRequest(data=1, timeout=1)
    squared_ubatch._requests_queue.put(data1)

    squared_ubatch._handler = mocker.Mock(return_value=[1, 2, 3])

    squared_ubatch._procces_in_batch()

    with pytest.raises(BadBatchOutputSize):
        data1.output


def test_procces_in_batch_raise_handler_not_set(squared_ubatch):
    squared_ubatch._handler = None

    with pytest.raises(HandlerNotSet):
        squared_ubatch._procces_in_batch()


def test_start_raise_handler_not_set(squared_ubatch):
    pass
