from typing import Callable, List

from ubatch.data_request import T, S
from ubatch.ubatch import UBatch


class VariableArgsFunction:
    def __call__(self, *args: List[T], **kwargs: List[T]) -> S: ...


class UBatchWrapper:
    def __init__(
        self, max_size: int, timeout: float, function: VariableArgsFunction
    ):
        """Wrapper around user function to add ubatch functionality

        Args:
            max_size (int): [description]
            timeout (float): [description]
            function (Callable[[List[T]], List[S]]): [description]
        """
        self.function: Callable[..., List[S]] = function
        self.max_size = max_size
        self.timeout = timeout
        self._mb = UBatch[T, S](max_size=self.max_size, timeout=self.timeout)
        self._mb.set_handler(self.function)
        self._mb.start()

    def ubatch(self, *arg: T, **kwargs: T) -> S:
        return self._mb.ubatch(*arg, **kwargs)

    def __call__(self, *arg: List[T], **kwargs: List[T]) -> List[S]:
        return self.function(*arg, **kwargs)


def ubatch_decorator(
    max_size: int, timeout: float
) -> Callable[[VariableArgsFunction], UBatchWrapper]:
    def wrap(function: VariableArgsFunction) -> UBatchWrapper:
        return UBatchWrapper(max_size, timeout, function)

    return wrap
