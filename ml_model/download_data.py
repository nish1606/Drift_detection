#!/usr/bin/env python3
"""Download the IEEE-CIS Fraud Detection dataset from Kaggle.

This script requires the Kaggle CLI to be installed and configured:
    pip install kaggle
    # Place your kaggle.json in ~/.kaggle/kaggle.json

Usage:
    python ml_model/download_data.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

DATASET = "ieee-fraud-detection"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "ieee-fraud-detection"
FILES = ["train_transaction.csv", "train_identity.csv"]


def check_kaggle_cli() -> bool:
    try:
        subprocess.run(["kaggle", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download() -> None:
    if not check_kaggle_cli():
        print("ERROR: Kaggle CLI is not installed or not configured.")
        print("Install: pip install kaggle")
        print("Configure: place kaggle.json in ~/.kaggle/kaggle.json")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {DATASET} to {OUTPUT_DIR}/ ...")
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(OUTPUT_DIR), "--unzip"],
        check=True,
    )

    missing = [f for f in FILES if not (OUTPUT_DIR / f).exists()]
    if missing:
        print(f"WARNING: Expected files not found after download: {missing}")
        sys.exit(1)

    print("Download complete.")
    print(f"Files ready at: {OUTPUT_DIR}/")
    for f in FILES:
        size_mb = (OUTPUT_DIR / f).stat().st_size / 1024 / 1024
        print(f"  {f}: {size_mb:.1f} MB")


if __name__ == "__main__":
    download()
