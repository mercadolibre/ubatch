import logging
import threading
import time
from queue import Empty, Queue
from typing import Callable, Generic, List, Optional

from ubatch.data_request import DataRequest, DataRequestBuffer, S, T

logger = logging.getLogger(__name__)


class BadBatchOutputSize(Exception):
    def __init__(self, input_size: int, output_size: int):
        """Raised when output size of handler differs from input size

        Args:
            input_size: Size of input
            output_size: Size of output
        """
        self.input_size = input_size
        self.output_size = output_size
        self.message = (
            f"Output size: {output_size} differs from the input size: {input_size}"
        )
        super().__init__(self.message)


class HandlerNotSet(Exception):
    """Raised when not handler is set in UBatch"""


class HandlerAlreadySet(Exception):
    """Raised when trying to change handler"""


class UBatch(Generic[T, S]):

    CHECK_INTERVAL = 0.002  # Time to wait (in seconds) if queue is empty.

    def __init__(self, max_size: int, timeout: float):
        """Join multiple individual inputs into one batch of inputs.

        Args:
            handler: User function that handle batches.
            max_size: Maximum size of inputs to pass to the handler.
            timeout: Maximum time (in seconds) to wait for inputs before
                starting to process them.
        """

        self.max_size = max_size  # Maximum size of handler inputs.
        self.timeout = timeout  # Maximum time (in seconds) of inputs to wait.

        self._handler: Optional[Callable[[List[T]], List[S]]] = None
        self._requests_queue: Queue[DataRequest[T, S]] = Queue()
        self._stop_thread: bool = False
        self._thread: Optional[threading.Thread] = None

    def set_handler(self, handler: Callable[[List[T]], List[S]]) -> None:
        """Set user function to handle inputs data

        Args:
            handler: Any callable to handle input data and return output data
        """
        if self._handler:
            raise HandlerAlreadySet()

        self._handler = handler

    def _wait_buffer_ready(self) -> DataRequestBuffer[T, S]:
        buffer = DataRequestBuffer[T, S](size=self.max_size)

        #  WARNING: This logic is difficult to understand and any change
        # can have an impact on performance.

        #  Get elements from queue until buffer is full or any element
        # in buffer reaches its expected life time in the queue."

        while not self._stop_thread:
            try:
                #  Get from queue as many elements as possible to fill buffer,
                # this prevents a queue full of elements that have reached the
                # lifetime from being processed one at a time.
                while not buffer.full():
                    buffer.append(self._requests_queue.get(block=False))
                else:
                    logger.debug("Buffer ready: buffer is full")
                    break
            except Empty:
                if buffer.time_is_over(future=self.CHECK_INTERVAL):
                    logger.debug("Buffer ready: An element in buffer near timeout")
                    break
                # Wait an interval of time before trying to get more elements
                # TODO: Use QUEUE_CHECK_INTERVAL
                time.sleep(self.CHECK_INTERVAL)

        return buffer

    def _procces_in_batch(self) -> None:
        """Process inputs in batch, stores output or exception in buffer.

        Blocks until batch is ready for being processed, when batch is ready
        call a handler to process input data, if an exceptions is raised on handler
        store exceptions into all DataRequest inside buffer, if exception isn't raised
        store returned value from handler on each individual DataRequest object.
        """
        if not self._handler:
            raise HandlerNotSet()

        start_at = time.time()
        buffer = self._wait_buffer_ready()
        elapsed_time = time.time() - start_at

        #  When _wait_for_ready_buffer is stopped buffer could be empty
        # avoid calling process_batch() with empty list.
        if not buffer:
            return

        buffer_size = len(buffer)

        try:
            input_data = buffer.get_inputs()

            start_at = time.time()
            batch_output = self._handler(input_data)
            elapsed_time = time.time() - start_at

            output_size = len(batch_output)

            if buffer_size != output_size:
                # This exception is going to be set in every DataRequest
                raise BadBatchOutputSize(buffer_size, output_size)

        except Exception as ex:
            logger.warning("An exception occurs processing %s inputs", buffer_size)
            buffer.set_exception(ex)
        else:
            buffer.set_outputs(batch_output)

            logger.debug("Process %s elements in %s seconds", buffer_size, elapsed_time)

    def _handle_request(self) -> None:  # pragma: no cover
        """Loop thread for processing inputs in batch."""
        while not self._stop_thread:
            self._procces_in_batch()

    def ubatch(self, data: T) -> S:
        """Add a new input to queue to being processed by handler in batches

        Wait and returns output value from handler.
        """
        if not self._thread:
            logger.warning("ubatch is not running")

        data_request = DataRequest[T, S](data=data, timeout=self.timeout)

        self._requests_queue.put(data_request)

        output = data_request.get_wait_output()

        logger.debug("Request ready: total time: %s", data_request.latency)

        return output

    def start(self) -> "UBatch[T, S]":  # pragma: no cover
        """Run handler on threads to process input data."""
        logger.info("Staring handler thread")
        if not self._handler:
            raise HandlerNotSet()

        self._stop_thread = False

        if not self._thread:
            self._thread = threading.Thread(target=self._handle_request)
            self._thread.setDaemon(True)
            self._thread.start()

        logger.info("Handler thread started")
        return self

    def stop(self) -> None:  # pragma: no cover
        """Run handler on threads to process input data."""
        logger.info("Stoping handler thread")

        self._stop_thread = True

        if self._thread:
            self._thread.join()
            self._thread = None

        logger.info("Handler thread stoped")
