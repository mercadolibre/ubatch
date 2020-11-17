import pytest
import time

from ubatch.data_request import DataRequest, DataRequestNotReady


@pytest.mark.timeout(10)
def test_ubatch_put_call_sleep_when_not_ready(mocker, squared_ubatch):
    data_request = DataRequest(data="data", timeout=10)
    data_request.output = "output_data"

    mocked_sleep = mocker.patch("time.sleep")
    mocker.patch(
        "ubatch.ubatch.DataRequest.ready", new_callable=mocker.PropertyMock
    ).side_effect = [False, True]

    data_request.get_wait_output()

    mocked_sleep.assert_called_once()


def test_datarequest_get_output_when_ready():
    data_request = DataRequest(data="data", timeout=10)
    data_request.output = "output_data"

    assert data_request.output == "output_data"


def test_datarequest_set_ready_true_when_output():
    data_request = DataRequest(data="data", timeout=10)
    data_request.output = "output_data"

    assert data_request.ready is True


def test_datarequest_set_ready_false_by_default():
    data_request = DataRequest(data="data", timeout=10)

    assert data_request.ready is False


def test_datarequest_outout_raise_notready_when_not_ready():
    data_request = DataRequest(data="data", timeout=10)

    with pytest.raises(DataRequestNotReady):
        data_request.output


def test_datarequest_exception_raise_notready_when_not_ready():
    data_request = DataRequest(data="data", timeout=10)

    with pytest.raises(DataRequestNotReady):
        data_request.exception


def test_datarequest_raise_exception_on_output_if_has_exception():
    data_request = DataRequest(data="data", timeout=10)
    data_request.exception = ValueError()

    with pytest.raises(ValueError):
        data_request.output


def test_datarequest_get_exception_when_ready():
    exception = Exception()
    data_request = DataRequest(data="data", timeout=10)
    data_request.exception = exception

    assert data_request.exception == exception


@pytest.mark.freeze_time("2018-09-07 16:35:00")
def test_datarequest_create_at_use_current_time(freezer):
    data_request = DataRequest(data="data", timeout=10)
    assert data_request._create_at == time.time()


@pytest.mark.freeze_time("2018-09-07 16:35:00")
def test_datarequest_elapsed_time_use_current_time(freezer):
    data_request = DataRequest(data="data", timeout=10)
    freezer.move_to("2018-09-07 16:35:05")
    assert data_request.elapsed_time() == 5


@pytest.mark.freeze_time("2018-09-07 16:35:00")
def test_datarequest_ttl_get_correct_ttl_in_seconds(freezer):
    data_request = DataRequest(data="data", timeout=20)
    freezer.move_to("2018-09-07 16:35:05")
    assert data_request.ttl() == 15


@pytest.mark.freeze_time("2018-09-07 16:35:00")
def test_datarequest_time_is_over_is_false_if_tll_is_larger_than_zero(freezer):
    data_request = DataRequest(data="data", timeout=50)
    freezer.move_to("2018-09-07 16:35:05")
    assert data_request.time_is_over() is False


@pytest.mark.freeze_time("2018-09-07 16:35:00")
def test_datarequest_time_is_over_is_false_if_tll_is_less_than_zero(freezer):
    data_request = DataRequest(data="data", timeout=5)
    freezer.move_to("2018-09-07 16:35:15")
    assert data_request.time_is_over() is True


@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_datarequest_ttl_is_in_s(freezer):
    data_request = DataRequest(data="data", timeout=5)
    freezer.move_to("2018-09-07 16:35:00.100")
    assert data_request.ttl() == pytest.approx(4.9)


@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_datarequest_elapsed_time_is_in_s(freezer):
    data_request = DataRequest(data="data", timeout=5)
    freezer.move_to("2018-09-07 16:35:00.200")
    assert data_request.elapsed_time() == pytest.approx(0.2)


def test_datarequest_latency_is_none_by_default():
    data_request = DataRequest(data="data", timeout=5)
    assert data_request.latency is None


@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_datarequest_output_set_latency_time(freezer):
    data_request = DataRequest(data="data", timeout=5)
    freezer.move_to("2018-09-07 16:35:00.200")
    data_request.output = "foo"
    assert data_request.latency == pytest.approx(0.2)


@pytest.mark.freeze_time("2018-09-07 16:35:00.000")
def test_datarequest_exception_set_latency_time(freezer):
    data_request = DataRequest(data="data", timeout=5)
    freezer.move_to("2018-09-07 16:35:00.200")
    data_request.exception = Exception()
    assert data_request.latency == pytest.approx(0.2)
