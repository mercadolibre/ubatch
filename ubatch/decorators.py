from typing import Callable, List

from ubatch.data_request import S, T
from ubatch.ubatch import UBatch


class UBatchWrapper:
    def __init__(
        self, max_size: int, timeout: float, function: Callable[[List[T]], List[S]]
    ):
        """Wrapper around user function to add ubatch functionality

        TODO: Stop UBatch thread

        Args:
            max_size (int): [description]
            timeout (float): [description]
            function (Callable[[List[T]], List[S]]): [description]
        """
        self.function = function
        self.max_size = max_size
        self.timeout = timeout
        self._mb = UBatch[T, S](max_size=self.max_size, timeout=self.timeout)
        self._mb.set_handler(self.function)
        self._mb.start()

    def ubatch(self, arg: T) -> S:
        return self._mb.ubatch(arg)

    def __call__(self, arg: List[T]) -> List[S]:
        return self.function(arg)


def ubatch_decorator(
    max_size: int, timeout: float
) -> Callable[[Callable[[List[T]], List[S]]], UBatchWrapper]:
    def wrap(function: Callable[[List[T]], List[S]]) -> UBatchWrapper:
        return UBatchWrapper(max_size, timeout, function)

    return wrap
