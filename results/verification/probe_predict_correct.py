import joblib
from backend.preprocessing.feature_engineering import FeatureEngineer

pipeline = joblib.load("backend/fraud_model.pkl")
engineer = FeatureEngineer()

for name, features in [
    ("risky", {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_1h": 9, "geo_distance": 900}),
    ("benign", {"amount": 15, "transaction_hour": 10, "country": "US", "velocity_1h": 0, "geo_distance": 2}),
]:
    engineered = engineer.build(features)
    engineered_vec = pipeline.named_steps["vectorizer"].transform([engineered])
    proba = pipeline.named_steps["model"].predict_proba(engineered_vec)[0]
    print(name, "engineered:", {k: round(float(v), 3) for k, v in engineered.items() if isinstance(v, (int, float))})
    print("   probability:", round(float(proba[1]), 4), "prediction:", int(proba[1] >= 0.5))