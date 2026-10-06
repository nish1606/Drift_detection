import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import DictVectorizer
from backend.preprocessing.feature_engineering import FeatureEngineer
import pandas as pd

shipped = joblib.load("backend/fraud_model.pkl")
names = list(shipped.named_steps["vectorizer"].get_feature_names_out())
coef = shipped.named_steps["model"].coef_[0]
intercept = float(shipped.named_steps["model"].intercept_[0])

engineer = FeatureEngineer()
for name, features in [
    ("risky", {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_1h": 9, "geo_distance": 900}),
    ("benign", {"amount": 15, "transaction_hour": 10, "country": "US", "velocity_1h": 0, "geo_distance": 2}),
]:
    engineered = engineer.build(features)
    x = shipped.named_steps["vectorizer"].transform([engineered])[0]
    score = float(x.dot(coef)) + intercept
    print(f"{name}: linear score = {score:+.4f}  proba = {1/(1+np.exp(-score)):.4f}")
    idx = names.index("amount_to_avg_ratio")
    print(f"   amount_to_avg_ratio={engineered['amount_to_avg_ratio']:.0f} x coef={coef[idx]:+.4f} = {engineered['amount_to_avg_ratio']*coef[idx]:+.2f}")

# Fresh fit on the shipped data to show what the coefficients should be.
frame = pd.read_csv("backend/data/transactions_realistic.csv")
features = frame.drop(columns=["isFraud"]).to_dict("records")
labels = frame["isFraud"].astype(int).tolist()
engineered_all = [engineer.build(r) for r in features]
vec = DictVectorizer()
X = vec.fit_transform(engineered_all)
fit_names = vec.get_feature_names_out()
model = LogisticRegression(max_iter=10000, class_weight="balanced").fit(X, labels)
fit_coef = model.coef_[0]
for feat in ("amount_to_avg_ratio", "amount_log", "velocity_spike", "geo_distance"):
    i = list(fit_names).index(feat)
    j = list(names).index(feat)
    print(f"fresh fit {feat:20s} coef={fit_coef[i]:+.4f}   shipped {feat:20s} coef={coef[j]:+.4f}")