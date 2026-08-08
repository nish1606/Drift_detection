import pandas as pd
from pathlib import Path

IEEE_TRANS = Path(__file__).resolve().parent.parent / "ieee-fraud-detection" / "train_transaction.csv"
IEEE_ID = Path(__file__).resolve().parent.parent / "ieee-fraud-detection" / "train_identity.csv"
OUT = Path(__file__).resolve().parent / "transactions_realistic.csv"

COLUMN_MAP = {
    "TransactionDT": "timestamp",
    "TransactionAmt": "amount",
    "card4": "merchant_category",
    "addr2": "geo_distance",
    "dist1": "velocity_1h",
    "dist2": "account_age_days",
    "C1": "avg_amount_last_30d",
}

def run(max_rows: int = 20000):
    if not IEEE_TRANS.exists() or not IEEE_ID.exists():
        raise FileNotFoundError("IEEE dataset not found")
    trans = pd.read_csv(IEEE_TRANS, usecols=list(COLUMN_MAP.keys()) + ["isFraud", "card1", "addr1"], nrows=max_rows)
    identity = pd.read_csv(IEEE_ID, usecols=["TransactionID", "id_33"], nrows=max_rows)
    df = trans.merge(identity, on="TransactionID", how="left")
    df = df.rename(columns=COLUMN_MAP)
    df["transaction_hour"] = (df["timestamp"] % 86400) // 3600
    df["is_foreign"] = df["addr1"].apply(lambda x: 1 if pd.notna(x) and x > 100 else 0)
    df["new_device"] = 0
    out = df[["timestamp", "amount", "transaction_hour", "is_foreign", "velocity_1h", "new_device", "account_age_days", "avg_amount_last_30d", "merchant_category", "geo_distance", "isFraud"]].copy()
    out.to_csv(OUT, index=False)
    print(f"Ingested {len(out)} rows to {OUT}")

if __name__ == "__main__":
    run()
