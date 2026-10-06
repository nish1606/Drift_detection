import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from backend.preprocessing.feature_engineering import FeatureEngineer

# Re-train on the shipped data the way run_experiments does, and compare the
# shipped model's coefficients against what the data actually implies.
frame = pd.read_csv("backend/data/transactions_realistic.csv")
features = frame.drop(columns=["isFraud"]).to_dict("records")
labels = frame["isFraud"].astype(int).tolist()
engineer = FeatureEngineer()
engineered = [engineer.build(record) for record in features]
print("fraud rate:", round(sum(labels) / len(labels), 4))

from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler

vectorizer = DictVectorizer()
X = vectorizer.fit_transform(engineered)
names = vectorizer.get_feature_names_out()
y = np.asarray(labels)

for scale in (False, True):
    scaler = StandardScaler(with_mean=False) if scale else None
    Xs = scaler.fit_transform(X) if scaler else X
    model = LogisticRegression(max_iter=10000, class_weight="balanced")
    model.fit(Xs, y)
    print(f"scale={scale}: intercept={model.intercept_[0]:+.4f} amount_log={model.coef_[0][names.tolist().index('amount_log')]:+.4f} geo_distance={model.coef_[0][names.tolist().index('geo_distance')]:+.4f} velocity_1h={model.coef_[0][names.tolist().index('velocity_1h')]:+.4f}")

# And what the shipped model predicts on the same engineered rows.
shipped = joblib.load("backend/fraud_model.pkl")
proba = shipped.predict_proba([engineered[i] for i in range(len(engineered))])[:, 1]
pred = (proba >= 0.5).astype(int)
from sklearn.metrics import accuracy_score, roc_auc_score
print("shipped on shipped data: accuracy", round(accuracy_score(y, pred), 4), "roc_auc", round(roc_auc_score(y, proba), 4))
print("shipped mean proba for fraud:", round(float(proba[y == 1].mean()), 4), "for non-fraud:", round(float(proba[y == 0].mean()), 4))