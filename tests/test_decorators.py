from ubatch.decorators import ubatch_decorator


def test_decorator_set_handler():
    @ubatch_decorator(max_size=5, timeout=0.5)
    def my_f(data_inputs):
        return [x ** 2 for x in data_inputs]

    assert my_f([3]) == [9]
    assert my_f.ubatch(5) == 25
