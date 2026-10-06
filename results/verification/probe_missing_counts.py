import pandas as pd

frame = pd.read_csv("backend/data/transactions_realistic.csv")
print("rows", len(frame))
for column in frame.columns:
    missing = int(frame[column].isna().sum())
    if missing:
        print(column, missing)