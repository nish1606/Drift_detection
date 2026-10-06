import pandas as pd

frame = pd.read_csv("backend/data/transactions_realistic.csv")
print("columns:", list(frame.columns))
print("isFraud counts:", frame["isFraud"].value_counts().to_dict())
print()
print(frame.groupby("isFraud")["amount"].agg(["count", "mean", "max"]).to_string())
print()
print(frame.groupby(["isFraud", "is_foreign"])["amount"].agg(["count", "mean"]).to_string())
print()
print(frame.groupby("isFraud")["transaction_hour"].agg(["count", "mean"]).to_string())