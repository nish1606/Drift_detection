"""Train an XGBoost model for fraud detection.
Usage:
  python train.py

Place `creditcard.csv` in `backend/data/creditcard.csv` if you want to use the Kaggle dataset.
If the file is missing the script will generate a small synthetic dataset for demo purposes.
"""
import os
import uuid
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score


DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "creditcard.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "fraud_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")
TRAIN_STATS = os.path.join(os.path.dirname(__file__), "train_stats.npz")
FEATURE_COLUMNS_PATH = os.path.join(os.path.dirname(__file__), "feature_columns.pkl")


def load_data():
    if os.path.exists(DATA_PATH):
        print("Loading dataset from", DATA_PATH)
        df = pd.read_csv(DATA_PATH)
        # Expecting Kaggle Credit Card Fraud format (V1..V28, Amount, Class)
        if 'Class' in df.columns:
            X = df.drop(columns=['Class'])
            y = df['Class']
            return X, y
    # Fallback: synthetic data
    print("Dataset not found; generating synthetic data for demo.")
    n = 20000
    rng = np.random.RandomState(42)
    amount = rng.exponential(scale=1000, size=n)
    country = rng.choice(['UK', 'US', 'FR', 'NG'], size=n, p=[0.6,0.2,0.15,0.05])
    new_device = rng.binomial(1, 0.05, size=n)
    # simple rule for fraud
    is_foreign = (country != 'UK').astype(int)
    fraud_prob = (amount > 2000).astype(float)*0.2 + is_foreign*0.25 + new_device*0.4
    fraud_prob = np.clip(fraud_prob, 0, 0.9)
    y = rng.binomial(1, fraud_prob)
    X = pd.DataFrame({
        'Amount': amount,
        'is_foreign': is_foreign,
        'new_device': new_device,
    })
    return X, pd.Series(y)


def train():
    X, y = load_data()
    X_processed = X.copy()

    for col in X_processed.columns:
        if not pd.api.types.is_numeric_dtype(X_processed[col]):
            X_processed[col] = X_processed[col].astype('category').cat.codes.astype(float)

    feature_columns = [col for col in X_processed.columns if pd.api.types.is_numeric_dtype(X_processed[col])]
    X_numeric = X_processed[feature_columns].copy().astype(float)
    y = y.astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X_numeric, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=100)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)

    print(f"precision={precision:.4f}")
    print(f"recall={recall:.4f}")
    print(f"f1={f1:.4f}")
    print(f"roc_auc={roc_auc:.4f}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(feature_columns, FEATURE_COLUMNS_PATH)

    # Save basic training distribution for `Amount` to be used by PSI
    if 'Amount' in X_numeric.columns:
        amounts = X_numeric['Amount'].values
        hist, bin_edges = np.histogram(amounts, bins=50)
        probs = hist.astype(float) / hist.sum()
        np.savez(TRAIN_STATS, bin_edges=bin_edges, probs=probs)

    # model version
    model_version = str(uuid.uuid4())
    meta = {'model_version': model_version}
    joblib.dump(meta, os.path.join(os.path.dirname(__file__), 'model_meta.pkl'))

    print("Model saved to", MODEL_PATH)


if __name__ == '__main__':
    train()
