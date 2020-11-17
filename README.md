# uBatch

**uBatch** is a simple, yet elegant library for processing any data in batch.

**uBatch** allow to process multiple inputs data from different threads
as a single block of data, this is useful when process data in a batch mode
has a lower cost than processing it independently, for example process data
in GPU or take advantage from optimization of libraries written in C. Ideally,
the code that processes the batches should release the Python GIL for allowing
others threads/coroutines to run, this is true in many C libraries wrapped in
Python.

Example

```python
>>> import threading
>>>
>>> from typing import List
>>> from ubatch import UBatch
>>>
>>>
>>> class Squeared:
...     def in_batch(self, data_inputs: List[int]) -> List[int]:
...         return [x ** 2 for x in data_inputs]
...
>>>
>>> squared = Squeared()
>>>
>>> squared_batch: UBatch[int, int] = UBatch(max_size=100, timeout=0.02)
>>> squared_batch.set_handler(handler=squared.in_batch)
>>> squared_batch.start()
>>>
>>>
>>> def thread_function(number: int) -> None:
...     result = squared_batch.get(number)
...     print(f"Input: {number}, Output: {result}")
...
>>>
>>> threads = []
>>> for i in range(10):
...     t = threading.Thread(target=thread_function, args=(i,))
...     threads.append(t)
...     t.start()
...
>>> for t in threads:
...     t.join()
Input: 0, Output: 0
Input: 4, Output: 16
Input: 9, Output: 81
Input: 5, Output: 25
Input: 2, Output: 4
Input: 1, Output: 1
Input: 6, Output: 36
Input: 3, Output: 9
Input: 8, Output: 64
Input: 7, Output: 49
```

The example above shows 10 threads calculating the square of a number, using
**uBatch** the threads delegate the calculation task to a single
process that calculates them in batch.

Example using **ubatch decorator**

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

# Installing uBatch and Supported Versions

```bash
$ pip install ubatch
```

uBatch officially supports Python 3.6+.

# Why using uBatch?

When data is processed offline it is easy to collect data to be processed at
same time, the same does not happen when requests are attended online as
example using Flask, this is where the uBatch potential comes in.

**TensorFlow** or **Scikit-learn** are just some of the libraries
that can take advantage of this functionality.

# uBatch and application server

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
$ gunicorn -k gevent app:app
```

Another example using **uBatch** to join multiple requests into one:

```python
import requests

from typing import List, Dict
from flask import Flask, request as flask_request
from flask_restx import Resource, Api

from ubatch import UBatch


app = Flask(__name__)
api = Api(app)

# FAKE_TITLE_MPI is am mpi that determines if a title is fake or not
FAKE_TITLE_MPI_URL = "http://my_mpi_url/predict"


def batch_fake_title_post(titles: List[str]) -> List[bool]:
    """Post a list of titles to MPI and return responses in a list"""

    # json_post example: {"predict": ["title1", "title2", "title3"]}
    json_post = {"predict": titles}

    # response example: {"predictions": [False, True. False]}
    response = requests.post(FAKE_TITLE_MPI_URL, json=json_post).json()

    # return: [False, True, False]
    return [x for x in response["predictions"]]


fake_title_batch: UBatch[str, bool] = UBatch(max_size=100, timeout=0.02)
fake_title_batch.set_handler(handler=batch_fake_title_post)
fake_title_batch.start()


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
$ gunicorn -k gevent app:app
```

# Start developing uBatch

Install poetry

```bash
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Clone repository

```bash
$ git clone git@github.com:mercadolibre/ubatch.git
```

Start shell

```bash
$ cd ubatch
$ poetry shell
$ poetry install
```

Run tests

```bash
$ pytest
```
