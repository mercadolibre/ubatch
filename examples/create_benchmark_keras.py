import logging
import time

import numpy as np

from keras.models import Sequential
from keras.layers import Dense

from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split


MODEL_FILENAME = "keras.h5"
INPUTS_FILENAME = "keras_inputs.csv"

N_SAMPLES = 10000
N_FEATURES = 100

logging.basicConfig()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


logger.info("Creating datasets")
X, y = make_regression(n_samples=N_SAMPLES, n_features=N_FEATURES, noise=0.1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)


logger.info("Training Keras model")
model = Sequential()
model.add(Dense(4, input_dim=N_FEATURES, activation="relu"))
model.add(Dense(4, activation="relu"))
model.add(Dense(1, activation="linear"))
model.compile(loss="mse", optimizer="adam")
model.fit(X_train, y_train, epochs=1000, verbose=0)

logger.info("Calculating mean time per prediction")

N = 1000
time_per_predict = []

for x in X_test[:N]:
    time_start = time.time()
    model.predict(np.array([x]))
    time_per_predict.append(time.time() - time_start)

logger.info("Mean time per prediction: %s", np.mean(time_per_predict))

logger.info("Dumping model into %s", MODEL_FILENAME)
model.save(MODEL_FILENAME)

logger.info("Dumping inputs into %s", INPUTS_FILENAME)
np.savetxt(INPUTS_FILENAME, X_test, delimiter=",")
