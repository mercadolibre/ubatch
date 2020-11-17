import random
import numpy as np
from typing import Dict, List

from fastapi import FastAPI  # type: ignore
from joblib import load

from sklearn.datasets import fetch_20newsgroups
from sklearn.model_selection import train_test_split

from microbatch import AsyncUBatch


ngd = fetch_20newsgroups(subset="all")

X = ngd.data
y = ngd.target
_, X_test, _, _ = train_test_split(X, y, test_size=0.33)


model = load("xgbregressor.joblib")


def predict(data: List[np.array]) -> List[np.float32]:
    return model.predict(np.array(data))  # type: ignore


preidct_ubatch = AsyncUBatch[List[np.array], np.float32](max_size=100, timeout=0.01)
preidct_ubatch.set_handler(predict)
preidct_ubatch.start()

app = FastAPI()


@app.post("/predict_ubatch")  # type: ignore
async def predict_ubatch_post() -> Dict[str, float]:
    output = await preidct_ubatch.ubatch(random.choice(X_test))
    return {"prediction": float(output)}


@app.post("/predict")  # type: ignore
def predict_post() -> Dict[str, float]:
    output = predict([random.choice(X_test)])[0]
    return {"prediction": float(output)}
