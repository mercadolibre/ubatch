import random
import numpy as np

from typing import Dict, List

from flask import Flask
from flask_restx import Resource, Api

# from numpy import genfromtxt

from ubatch import ubatch_decorator

# from keras.models import load_model
from sklearn.datasets import fetch_20newsgroups
from sklearn.model_selection import train_test_split


from joblib import load

ngd = fetch_20newsgroups(subset="all")

X = ngd.data
y = ngd.target
_, X_test, _, _ = train_test_split(X, y, test_size=0.33)


model = load("xgbregressor.joblib")
# X_test = genfromtxt("xgbregressor_inputs.csv", delimiter=",")

app = Flask(__name__)
api = Api(app)


@ubatch_decorator(max_size=100, timeout=0.01)
def predict(data: List[np.array]) -> List[np.float32]:
    return model.predict(np.array(data))  # type: ignore


@api.route("/predict_ubatch")
class BatchPredict(Resource):
    def post(self) -> Dict[str, float]:
        output = predict.ubatch(random.choice(X_test))
        return {"prediction": float(output)}


@api.route("/predict")
class Predict(Resource):
    def post(self) -> Dict[str, float]:
        output = predict([random.choice(X_test)])[0]
        return {"prediction": float(output)}
