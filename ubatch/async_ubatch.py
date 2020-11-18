import asyncio
import concurrent.futures
import logging
import time
from collections import deque
from functools import partial
from typing import Callable, Deque, Generic, List, Optional

from ubatch.data_request import DataRequest, DataRequestBuffer, S, T
from ubatch.exceptions import BadBatchOutputSize, HandlerAlreadySet, HandlerNotSet

logger = logging.getLogger(__name__)


CHECK_INTERVAL = 0.001  # Time to wait (in seconds) if queue is empty.
MONITOR_INTERVAL = 5  # Time to wait (in seconds) for logging statistics.


class AsyncUBatch(Generic[T, S]):
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
        # TODO: let select users if run in thread or process,
        # some c libs release GIL, what about corrutine?
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._queue: Deque[DataRequest[T, S]] = deque()
        self.pending: int = 0  # Pending batch to being processed

    async def _monitor(self) -> None:
        while True:
            logging.info(
                "queue size: %s, pending batch: %s", len(self._queue), self.pending
            )
            await asyncio.sleep(MONITOR_INTERVAL)

    def set_handler(self, handler: Callable[[List[T]], List[S]]) -> None:
        """Set user function to handle inputs data

        Args:
            handler: Any callable to handle input data and return output data
        """
        if self._handler:
            raise HandlerAlreadySet()

        self._handler = handler

    async def _run_in_executor(self, buffer: DataRequestBuffer[T, S]) -> None:
        if not self._handler:
            raise HandlerNotSet

        loop = asyncio.get_event_loop()

        logging.debug("process send to pool with buffer: %s", buffer)
        data = [x.data for x in buffer]

        try:
            self.pending += 1
            # TODO: python 3.9 asyncio.to_thread
            outputs = await loop.run_in_executor(
                self._executor, partial(self._handler, data)
            )
            self.pending -= 1

            if len(outputs) != len(data):
                # This exception is going to be set in every DataRequest
                raise BadBatchOutputSize(len(data), len(outputs))
        except Exception as ex:
            for dr in buffer:
                dr.exception = ex
        else:
            for dr, o in zip(buffer, outputs):
                dr.output = o

        logging.debug("end pool with buffer: %s", buffer)

    async def _process_queue(self) -> None:
        loop = asyncio.get_event_loop()

        while True:
            buffer = DataRequestBuffer[T, S](size=self.max_size)

            # Wait for at least 1 item is in buffer
            while len(buffer) < 1:
                try:
                    buffer.append(self._queue.pop())
                except IndexError:
                    await asyncio.sleep(CHECK_INTERVAL)

            _timeout = time.time() + self.timeout
            _timeouted = False

            while not (buffer.full() or _timeouted):
                _timeouted = time.time() > _timeout
                try:
                    buffer.append(self._queue.pop())
                except IndexError:
                    await asyncio.sleep(CHECK_INTERVAL)

            # If thread/process is busy keep adding elements to buffer
            while not (buffer.full() or self.pending != 0):
                try:
                    buffer.append(self._queue.pop())
                except IndexError:
                    await asyncio.sleep(CHECK_INTERVAL)

            if buffer:
                logging.debug("processing (len): %s", len(buffer))
                loop.create_task(self._run_in_executor(buffer))

    async def ubatch(self, data: T) -> S:
        # Async UBatch do not use DataRequest timeout
        data_request = DataRequest[T, S](data=data, timeout=0)

        self._queue.append(data_request)

        while not data_request.ready:
            await asyncio.sleep(CHECK_INTERVAL)

        logger.debug("Request ready: total time: %s", data_request.latency)

        return data_request.output

    def start(self) -> "AsyncUBatch[T, S]":  # pragma: no cover
        if not self._handler:
            raise HandlerNotSet()

        loop = asyncio.get_event_loop()

        loop.create_task(self._monitor())
        loop.create_task(self._process_queue())

        return self
