"""Benchmark POST /predict latency with 200 sequential requests."""
from __future__ import annotations

import time
import urllib.request
import json

LOGIN_URL = "http://127.0.0.1:8000/api/v1/auth/login"
PREDICT_URL = "http://127.0.0.1:8000/api/v1/predict"
USERNAME = "analyst"
PASSWORD = "analyst123"
REQUESTS = 20

FEATURES = {
    "amount": 1200.0,
    "transaction_hour": 23.0,
    "is_foreign": 1.0,
    "velocity_1h": 5.0,
    "new_device": 1.0,
    "account_age_days": 30.0,
    "avg_amount_last_30d": 800.0,
    "merchant_category": "travel",
    "geo_distance": 150.0,
}


def get_token() -> str:
    data = f"username={USERNAME}&password={PASSWORD}".encode()
    req = urllib.request.Request(LOGIN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["access_token"]


def predict(token: str) -> tuple[int, float]:
    body = json.dumps({"model_name": "fraud_classifier", "features": FEATURES}).encode()
    req = urllib.request.Request(PREDICT_URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }, method="POST")
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
    elapsed_ms = (time.perf_counter() - start) * 1000
    data = json.loads(raw)
    return int(data.get("prediction", -1)), elapsed_ms


def main() -> None:
    token = get_token()
    latencies: list[float] = []
    decisions: list[int] = []

    for _ in range(REQUESTS):
        prediction, elapsed = predict(token)
        decisions.append(prediction)
        latencies.append(elapsed)

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    mean_latency = sum(latencies) / len(latencies)

    print(f"Requests: {REQUESTS}")
    print(f"Mean latency: {mean_latency:.2f} ms")
    print(f"P50: {p50:.2f} ms")
    print(f"P95: {p95:.2f} ms")
    print(f"P99: {p99:.2f} ms")
    print(f"Decisions: {sum(1 for d in decisions if d == 1)} block, {sum(1 for d in decisions if d == 0)} legitimate")
    print(f"Target: 200 ms")
    print(f"P95 PASS: {p95 < 200}")


if __name__ == "__main__":
    main()
