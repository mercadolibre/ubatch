import pytest

from threading import Thread
from time import sleep

from ubatch.ubatch import UBatch


class MyTestException(Exception):
    """Use to test if an exceptions occurs process/thread continue running"""

    pass


def in_batch(input_data):
    if 6 in input_data:
        raise MyTestException
    return [x ** 2 for x in input_data]


@pytest.mark.no_cover  # TODO: not working!
@pytest.mark.timeout(5)
def test_multiple_put_outputs_consumed_at_once(reraise, mocker):
    """Test multiple thread using UBatch at same time

    Simulate multiple put at same time, process batch should be called once
    with all inputs.

    UBatch._wait_buffer_ready logic ensure all elements in queue will
    be consumed after checking timeout, this allow to put elements in queue
    before starting UBatch simulating a constant flow of inputs in
    UBatch.

    Scenario:
        11 threads put integers from 0 to 10 at same time, batch will be
        consumed from 5 to 5 (max_batch_size). What happens is that
        process_batch need to be called 3 times, first call has to be with
        [0, 1, 2, 3, 4], second time call has to be with [5, 6, 7, 8, 9] and
        the last call has to be with [10]

    Use reraise to fail test if any thread assert false
    """
    N_THREADS = 11
    MAX_SIZE = 5
    TIMEOUT = 0.1

    mb = UBatch(max_size=MAX_SIZE, timeout=TIMEOUT)
    mb.set_handler(handler=in_batch)

    process_batch_spy = mocker.spy(mb, "_handler")

    # Simulate threads waiting for outputs
    def run(i):
        with reraise:
            try:
                output = mb.ubatch(i)
            except MyTestException:
                if i in [5, 6, 7, 8, 9]:
                    assert True
                else:
                    assert False
            else:
                # Test output received by thread is what we expect
                assert output == i ** 2

    # Create 5 threads waiting for outputs, this simulate flask thread
    threads = [Thread(target=run, args=(i,)) for i in range(N_THREADS)]

    # Start thread before staring UBatch process. ensuring queue
    # have all threads data and process all data in only one batch.
    # TODO: This assumes that thread start in order, so inputs will
    # be 1, 2, 3, ...
    for t in threads:
        sleep(0.1)
        t.start()

    try:
        mb.start()
        # Wait for threads to get outputs
        for t in threads:
            t.join()
    except Exception:
        assert False
    finally:
        mb.stop()

    calls = [
        mocker.call([0, 1, 2, 3, 4]),
        mocker.call([5, 6, 7, 8, 9]),
        mocker.call([10]),
    ]
    process_batch_spy.assert_has_calls(calls)
    assert process_batch_spy.call_count == 3
