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
    """Raised when not handler is set in MicroBatch"""


class HandlerAlreadySet(Exception):
    """Raised when trying to change handler"""
