import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IEEE_DIR = BASE_DIR / "ieee-fraud-detection"

REQUIRED_FILES = {
    DATA_DIR / "transactions_synthetic.csv": "synthetic transactions",
    DATA_DIR / "transactions_realistic.csv": "realistic transactions",
    DATA_DIR / "transactions_realistic_schema.json": "schema",
    DATA_DIR / "drift_scenario.csv": "drift scenario",
    IEEE_DIR / "train_transaction.csv": "IEEE transactions",
    IEEE_DIR / "train_identity.csv": "IEEE identity",
}

for path, label in REQUIRED_FILES.items():
    if not path.exists():
        print(f"MISSING {label}: {path}")
    else:
        print(f"OK {label}: {path}")
