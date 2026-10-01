"""Benchmark POST /predict latency with configurable sequential requests.

For benchmarks above 60 requests per minute, raise RATE_LIMIT_PER_MINUTE
(for example, to 100000); this changes only the benchmarking setting.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request

LOGIN_URL = "http://127.0.0.1:8000/api/v1/auth/login"
PREDICT_URL = "http://127.0.0.1:8000/api/v1/predict"
USERNAME = "analyst"
PASSWORD = "analyst123"
DEFAULT_REQUESTS = 20

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


def get_token(base_url: str) -> str:
    data = f"username={USERNAME}&password={PASSWORD}".encode()
    req = urllib.request.Request(f"{base_url}/api/v1/auth/login", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["access_token"]


def predict(token: str, base_url: str) -> tuple[int, float]:
    body = json.dumps({"model_name": "fraud_classifier", "features": FEATURES}).encode()
    req = urllib.request.Request(f"{base_url}/api/v1/predict", data=body, headers={
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS)
    parser.add_argument("--warmup", type=int, default=0)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    token = get_token(base_url)
    for _ in range(args.warmup):
        try:
            predict(token, base_url)
        except Exception:
            pass
    latencies: list[float] = []
    successful = 0
    failed = 0
    wall_start = time.perf_counter()

    for _ in range(args.requests):
        try:
            _, elapsed = predict(token, base_url)
            successful += 1
            latencies.append(elapsed)
        except Exception:
            failed += 1

    wall_seconds = time.perf_counter() - wall_start
    if not latencies:
        print(f"Requests: {args.requests} (n=0 successful samples)")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        return
    latencies.sort()
    sample_count = len(latencies)
    percentile = lambda value: latencies[min(int(sample_count * value), sample_count - 1)]
    p50 = percentile(0.50)
    p95 = percentile(0.95)
    p99 = percentile(0.99)
    mean_latency = sum(latencies) / len(latencies)

    print(f"Requests: {args.requests} (n={sample_count} successful samples)")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Mean latency: {mean_latency:.2f} ms")
    print(f"P50: {p50:.2f} ms")
    print(f"P95: {p95:.2f} ms")
    print(f"P99: {p99:.2f} ms")
    print(f"Min: {latencies[0]:.2f} ms")
    print(f"Max: {latencies[-1]:.2f} ms")
    print(f"Sequential throughput: {successful / wall_seconds:.2f} requests/sec")


if __name__ == "__main__":
    main()
