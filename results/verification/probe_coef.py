import joblib
import numpy as np

pipeline = joblib.load("backend/fraud_model.pkl")
estimator = pipeline.named_steps["model"]
names = pipeline.named_steps["vectorizer"].get_feature_names_out()
for name, coef in sorted(zip(names, estimator.coef_[0]), key=lambda item: -abs(item[1]))[:12]:
    print(f"{name:30s} {coef:+.4f}")
print("intercept:", round(float(estimator.intercept_[0]), 4))
print("classes:", estimator.classes_)