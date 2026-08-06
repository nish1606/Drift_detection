from __future__ import annotations


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_endpoint(client):
    response = client.post(
        "/api/v1/predict",
        json={
            "model_name": "fraud_classifier",
            "features": {
                "amount": 1200,
                "transaction_hour": 23,
                "high_risk_country": 1,
                "velocity_spike": 1,
                "new_device": 1,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] in {"allow", "review", "block", "freeze"}
    assert 0.0 <= payload["probability"] <= 1.0
