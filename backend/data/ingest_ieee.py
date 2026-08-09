from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
IEEE_TRANS = PROJECT_ROOT / "ieee-fraud-detection" / "train_transaction.csv"
IEEE_ID = PROJECT_ROOT / "ieee-fraud-detection" / "train_identity.csv"
OUT = BASE_DIR / "transactions_realistic.csv"

COLUMN_MAP = {
    "TransactionDT": "timestamp",
    "TransactionAmt": "amount",
    "card4": "merchant_category",
    "addr2": "geo_distance",
    "dist1": "velocity_1h",
    "dist2": "account_age_days",
    "C1": "avg_amount_last_30d",
}

SEARCH_PATHS = [
    PROJECT_ROOT / "ieee-fraud-detection",
    PROJECT_ROOT / "data" / "ieee",
    PROJECT_ROOT / "ml_model" / "data",
    BASE_DIR,
]


def _find_ieee_files():
    for directory in SEARCH_PATHS:
        trans = directory / "train_transaction.csv"
        identity = directory / "train_identity.csv"
        if trans.exists() and identity.exists():
            return trans, identity
        trans = directory / "transactions.csv"
        identity = directory / "identity.csv"
        if trans.exists() and identity.exists():
            return trans, identity
    return None, None


def run(max_rows: int = 20000):
    ieee_trans, ieee_id = _find_ieee_files()
    if ieee_trans is None or ieee_id is None:
        print("IEEE dataset not found. Place your files in one of these locations:")
        for path in SEARCH_PATHS:
            print(f"  {path / 'train_transaction.csv'}")
            print(f"  {path / 'train_identity.csv'}")
        raise FileNotFoundError("IEEE dataset not found")
    trans = pd.read_csv(ieee_trans, usecols=list(COLUMN_MAP.keys()) + ["isFraud", "card1", "addr1", "TransactionID"], nrows=max_rows)
    identity = pd.read_csv(ieee_id, usecols=["TransactionID", "id_33"], nrows=max_rows)
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
