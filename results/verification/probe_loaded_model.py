import joblib
import numpy as np
from pathlib import Path

path = Path("backend/fraud_model.pkl")
print("exists:", path.exists(), "size:", path.stat().st_size if path.exists() else None)
pipeline = joblib.load(path)
print("steps:", list(pipeline.named_steps))
estimator = pipeline.named_steps["model"]
print("classes:", estimator.classes_)
print("coef:", np.round(estimator.coef_[0], 4))
print("intercept:", round(float(estimator.intercept_[0]), 4))

for name, features in [
    ("risky", {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_1h": 9, "geo_distance": 900}),
    ("benign", {"amount": 15, "transaction_hour": 10, "country": "US", "velocity_1h": 0, "geo_distance": 2}),
]:
    engineered = pipeline.named_steps["vectorizer"].transform([features])
    if "scaler" in pipeline.named_steps:
        engineered = pipeline.named_steps["scaler"].transform(engineered)
    proba = estimator.predict_proba(engineered)[0]
    print(name, "proba:", np.round(proba, 4), "prediction:", estimator.predict(engineered)[0])