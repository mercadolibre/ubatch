# uBatch

**uBatch** is a simple, yet elegant library for processing streams data in micro batches.

**uBatch** allow to process multiple inputs data from different threads
as a single block of data, this is useful when process data in a batches
has a lower cost than processing it independently, for example process data
in GPU or take advantage from optimization of libraries written in C. Ideally,
the code that processes the batches should release the Python GIL for allowing
others threads/coroutines to run, this is true in many C libraries wrapped in
Python.

[![Documentation Status](https://readthedocs.org/projects/ubatch/badge/?version=latest)](https://ubatch.readthedocs.io/en/latest/?badge=latest)

Example

```python
>>> import threading
>>>
>>> from typing import List
>>> from ubatch import ubatch_decorator
>>>
>>>
>>> @ubatch_decorator(max_size=5, timeout=0.01)
... def squared(a: List[int]) -> List[int]:
...     print(a)
...     return [x ** 2 for x in a]
...
>>>
>>> inputs = list(range(10))
>>>
>>> # Run squared as usual
... _ = squared(inputs)
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
>>>
>>>
>>> def thread_function(number: int) -> None:
...     _ = squared.ubatch(number)
...
>>>
>>> # Multiple threads squared individual inputs
... threads = []
>>> for i in inputs:
...     t = threading.Thread(target=thread_function, args=(i,))
...     threads.append(t)
...     t.start()
...
[0, 1, 2, 3, 4]
[5, 6, 7, 8, 9]
>>> for t in threads:
...     t.join()
```

The example above shows 10 threads calculating the square of a number, using
**uBatch** the threads delegate the calculation task to a single
process that calculates them in batch.


And with multiple parameters in user method

```python
>>> import threading
>>> 
>>> from typing import List
>>> from ubatch import ubatch_decorator
>>> 
>>> 
>>> @ubatch_decorator(max_size=5, timeout=0.01)
... def squared_cube(a: List[int], mode: List[str]) -> List[int]:
...     print(a)
...     print(mode)
...     return [x ** 2 if y == 'square' else x ** 3 for x, y in zip(a, mode)]
... 
>>> 
>>> inputs = list(range(10))
>>> modes = ['square' if i % 2 == 0 else 'cube' for i in inputs]
>>> 
>>> # Run function as usual
>>> _ = squared_cube(inputs, modes)
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
['square', 'cube', 'square', 'cube', 'square', 'cube', 'square', 'cube', 'square', 'cube']
>>> 
>>> 
>>> def thread_function(number: int, mode: str) -> None:
...     _ = squared_cube.ubatch(number, mode)
... 
>>> 
>>> # Multiple threads squared individual inputs
... threads = []
>>> for i,j in zip(inputs, modes):
...     t = threading.Thread(target=thread_function, args=(i,j))
...     threads.append(t)
...     t.start()
...     
[0, 1, 2, 3, 4]
['square', 'cube', 'square', 'cube', 'square']
[5, 6, 7, 8, 9]
['cube', 'square', 'cube', 'square', 'cube']
>>> for t in threads:
...     t.join()
```

This example is pretty similar to the previous one, the only difference is
that the decorated function receives an additional parameter and **uBatch** 
is able to support a variable number of parameters. 

If you have a function with a parameter that doesn't need to be accumulated, 
with every call you can use the python "partial" tool before the use of 
ubatch_decorator.

```python
>>> import threading
>>> 
>>> from functools import partial
>>> from typing import List, Any
>>> from ubatch import ubatch_decorator
>>> 
>>> 
>>> def squared_cube(model: Any, a: List[int], mode: List[str]) -> List[int]:
...     print(a)
...     print(mode)
...     return [x ** 2 if y == 'square' else x ** 3 for x, y in zip(a, mode)]
... 
>>> squared_cube = partial(squared_cube, 'This is a model')
>>> squared_cube = ubatch_decorator(max_size=5, timeout=0.01)(squared_cube)
... ...
```

The code after that can remains like in the previous example.

## Installing uBatch and Supported Versions

```bash
pip install ubatch
```

uBatch officially supports Python 3.6+.

## Why using uBatch

When data is processed offline it is easy to collect data to be processed at
same time, the same does not happen when requests are attended online as
example using Flask, this is where the uBatch potential comes in.

**TensorFlow** or **Scikit-learn** are just some of the libraries
that can take advantage of this functionality.

## uBatch and application server

Python application servers work like this:

When the server is initialized multiple processes are created and each process
create a bunch of threads for handling requests. Taking advantage of those
threads that run in parallel **uBatch** can be used to group several
inputs and process them in a single block.

Let's see a Flask example:

```python
import numpy as np

from typing import List, Dict
from flask import Flask, request as flask_request
from flask_restx import Resource, Api

from ubatch import UBatch
from model import load_model


app = Flask(__name__)
api = Api(app)

model = load_model()

predict_batch: UBatch[np.array, np.array] = UBatch(max_size=50, timeout=0.01)
predict_batch.set_handler(handler=model.batch_predict)
predict_batch.start()


@api.route("/predict")
class Predict(Resource):
    def post(self) -> Dict[str, List[float]]:
        received_input = np.array(flask_request.json["input"])
        result = predict_batch.ubatch(received_input)

        return {"prediction": result.tolist()}
```

Start application server:

```bash
gunicorn -k gevent app:app
```

Another example using **uBatch** to join multiple requests into one:

```python
import requests

from typing import List, Dict
from flask import Flask, request as flask_request
from flask_restx import Resource, Api

from ubatch import ubatch_decorator


app = Flask(__name__)
api = Api(app)

FAKE_TITLE_MPI_URL = "http://my_mpi_url/predict"

@ubatch_decorator(max_size=100, timeout=0.03)
def batch_fake_title_post(titles: List[str]) -> List[bool]:
    """Post a list of titles to MPI and return responses in a list"""

    # json_post example: {"predict": ["title1", "title2", "title3"]}
    json_post = {"predict": titles}

    # response example: {"predictions": [False, True. False]}
    response = requests.post(FAKE_TITLE_MPI_URL, json=json_post).json()

    # return: [False, True, False]
    return [x for x in response["predictions"]]

@api.route("/predict")
class Predict(Resource):
    def post(self) -> Dict[str, bool]:
        # title example: "Title1"
        title = flask_request.json["title"]

        # prediction example: False
        prediction = fake_title_batch.ubatch(title)

        return {"prediction": prediction}
```

Start application server:

```bash
gunicorn -k gevent app:app
```

## Start developing uBatch

Install poetry

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Clone repository

```bash
git clone git@github.com:mercadolibre/ubatch.git
```

Start shell and install dependencies

```bash
cd ubatch
poetry shell
poetry install
```

Run tests

```bash
pytest
```

Building docs

```bash
cd ubatch/docs
poetry shell
make html
```

## Licensing

**uBatch** is licensed under the Apache License, Version 2.0.
See [LICENSE](https://github.com/mercadolibre/ubatch/blob/master/docs/LICENSE) for the full license text.