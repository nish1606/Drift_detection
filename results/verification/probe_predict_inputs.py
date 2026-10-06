import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.status, json.loads(response.read() or b"null")


login = urllib.request.Request(
    f"{BASE}/api/v1/auth/login", data=b"username=analyst&password=analyst123", method="POST"
)
with urllib.request.urlopen(login, timeout=30) as response:
    token = json.loads(response.read())["access_token"]

for name, features in [
    ("risky", {"amount": 9000, "transaction_hour": 23, "country": "NG", "velocity_1h": 9, "geo_distance": 900}),
    ("benign", {"amount": 15, "transaction_hour": 10, "country": "US", "velocity_1h": 0, "geo_distance": 2}),
]:
    status, body = call("POST", "/api/v1/predict", {"features": features}, token)
    print(name, "decision:", body["decision"], "probability:", round(body["probability"], 4), "risk_score:", round(body["risk_score"], 4), "alerts:", len(body["alerts"]))
    if body["alerts"]:
        print("   ", body["alerts"][0])