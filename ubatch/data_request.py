import time
from typing import Generic, Iterator, List, Optional, TypeVar

T = TypeVar("T")
S = TypeVar("S")


OUTPUT_CHECK_INTERVAL: float = 0.001  # Time to wait (in seconds) for output.


class DataRequestNotReady(Exception):
    """Raised when trying to access a data_request without a defined
    output or exception.
    """


class DataRequestBufferFull(Exception):
    """Raised when trying to append data_request on fulled
    buffer.
    """


class DataRequest(Generic[T, S]):
    def __init__(self, data: T, timeout: float):
        """Handles user input data that will be processed in a queue.
        Stores output or exceptions that may occurs during the handling
        of the request.

        This class ensures that the output will not be accessible if:

        1) It was not previously set by other process.
        2) An Exception is set.

        Also tracks the lifetime and the time that has passed since its
        creation.

        Examples:

        Handle output data:

            >>> data_request = DataRequest(data="foo", timeout=10)
            >>> data_request.ready
            False
            >>> data_request.output = "bar"
            >>> data_request.ready
            True

        Accessing output of data not ready:

            >>> data_request = DataRequest(data="foo", timeout=10)
            >>> data_request.output
            raise DataRequestNotReady

        Passing exception as output:

            >>> data_request = DataRequest(data="foo", timeout=10)
            >>> data_request.exception = ValueError("bar")
            >>> data_request.output
            raise ValueError("bar")

        Args:
            data: User input data.
            timeout: Maximum expected time (in seconds) for this request in queue.
        """
        self.data = data  # User input data
        self.timeout = timeout  # Maximum time waiting without being processed

        self._ready: bool = False  # True when output data is set.
        self._create_at: float = time.time()  # This object creation time.

        self._latency: Optional[float] = None  # Time from creation time to output.
        self._exception: Optional[Exception] = None  # Exception of processed data.

    def _set_ready(self) -> None:
        """Set latency time and readiness to this request."""
        self._latency = self.elapsed_time()
        self._ready = True

    def time_is_over(self) -> int:
        """True if TTL is less than 0."""
        return self.ttl() <= 0

    def elapsed_time(self) -> float:
        """Measure time passed since this object was created."""
        return time.time() - self._create_at

    def ttl(self) -> float:
        """Measures how long until the timeout is fulfilled."""
        return self.timeout - self.elapsed_time()

    @property
    def ready(self) -> bool:
        """True only when output data or exception is set."""
        return self._ready

    @property
    def output(self) -> S:
        """Get current output value if any.

        Raises:
            DataRequestNotReady: If output or exception was not set.
            Exception: If any exception is set instead of output.

        Returns:
            S: Output data
        """
        if not self._ready:
            raise DataRequestNotReady
        if self._exception:
            raise self._exception

        return self._output

    @output.setter
    def output(self, data: S) -> None:
        """Set current request output and ready flag to True."""
        self._output = data
        self._set_ready()

    def get_wait_output(self, check_interval: float = OUTPUT_CHECK_INTERVAL) -> S:
        """Wait and get output of data request

        TODO: Set and raise timeout

        Args:
            wait: Wait for output ready. Defaults to True.

        Returns:
            S: Output data
        """
        while not self.ready:
            time.sleep(check_interval)

        return self.output

    @property
    def exception(self) -> Optional[Exception]:
        """Get exception set in this request if Any.

        Raises:
            DataRequestNotReady: If output or exception was not set.
        """
        if not self._ready:
            raise DataRequestNotReady

        return self._exception

    @exception.setter
    def exception(self, exception: Exception) -> None:
        """Set current request exception and ready flag to True."""
        self._exception = exception
        self._set_ready()

    @property
    def latency(self) -> Optional[float]:
        """Time from creation to output set."""
        return self._latency


class DataRequestBuffer(Generic[T, S]):
    def __init__(self, size: int):
        self._size = size
        self._buffer: List[DataRequest[T, S]] = []

    def __iter__(self) -> Iterator[DataRequest[T, S]]:
        return iter(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)

    def append(self, data: DataRequest[T, S]) -> None:
        if self.full():
            raise DataRequestBufferFull()

        self._buffer.append(data)

    def time_is_over(self, future: float = 0) -> bool:
        """Check if any element of the buffer will meet the expected lifetime
        in the future.

        Args:
            future (float, optional):
                [Time (in seconds) to check expected lifetime in future].
                Defaults to 0.

        Returns:
            bool: True is any element in buffer will timeout in future.
        """
        return any(data_request.ttl() <= future for data_request in self)

    def full(self) -> bool:
        return len(self) >= self._size

    def get_inputs(self) -> List[T]:
        return [data_request.data for data_request in self]

    def set_outputs(self, outputs: List[S]) -> None:
        for data_request, output in zip(self, outputs):
            data_request.output = output

    def set_exception(self, exception: Exception) -> None:
        for data_request in self:
            data_request.exception = exception

    def space_left(self) -> int:
        return self._size - len(self)

    def clear(self) -> None:
        self._buffer = []
