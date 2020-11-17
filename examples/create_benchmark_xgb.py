import logging
import time

import numpy as np
import xgboost as xgb

from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from joblib import dump

logging.basicConfig()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203


logger.info("Creating datasets")
ngd = fetch_20newsgroups(subset="all")
X = ngd.data
y = ngd.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)


MODEL_FILENAME = "xgbregressor.joblib"
INPUTS_FILENAME = "xgbregressor_inputs.csv"

logger.info("Training XGBRegressor model")

# model = Pipeline(
#     [
#         ("vectorizer", TfidfVectorizer()),
#         (
#             "xgbrg",
#             xgb.XGBRegressor(
#                 colsample_bytree=0.4,
#                 gamma=0,
#                 learning_rate=0.07,
#                 max_depth=3,
#                 min_child_weight=1.5,
#                 n_estimators=10000,
#                 reg_alpha=0.75,
#                 reg_lambda=0.45,
#                 subsample=0.6,
#                 seed=42,
#             ),
#         ),
#     ]
# )
model = Pipeline(
    [
        ("vect", CountVectorizer()),
        ("tfidf", TfidfTransformer()),
        ("clf", xgb.XGBClassifier()),
    ]
)

model.fit(X_train, y_train)

logger.info("Calculating mean time per prediction")

N = 1000
time_per_predict = []

for x in X_test[:N]:
    time_start = time.time()
    model.predict(np.array([x]))
    time_per_predict.append(time.time() - time_start)


logger.info("Mean time per prediction: %s", np.mean(time_per_predict))

N = 1000
time_per_predict = []


for x in chunks(X_test[:N], 20):
    time_start = time.time()
    model.predict(np.array(x))
    time_per_predict.append(time.time() - time_start)

logger.info("Mean time per (20) prediction: %s", np.mean(time_per_predict))


N = 1000
time_per_predict = []


for x in chunks(X_test[:N], 100):
    time_start = time.time()
    model.predict(np.array(x))
    time_per_predict.append(time.time() - time_start)

logger.info("Mean time per (100) prediction: %s", np.mean(time_per_predict))


N = 1000
time_per_predict = []


for x in chunks(X_test[:N], 200):
    time_start = time.time()
    model.predict(np.array(x))
    time_per_predict.append(time.time() - time_start)

logger.info("Mean time per (200) prediction: %s", np.mean(time_per_predict))


logger.info("Dumping model into %s", MODEL_FILENAME)
dump(model, MODEL_FILENAME)

# logger.info("Dumping inputs into %s", INPUTS_FILENAME)
# np.savetxt(INPUTS_FILENAME, X_test, delimiter=",")
