"""Live check that freeze/rollback are reachable and audited over HTTP."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent / "step4_response_state_live.json"


def call(method: str, path: str, body=None, token: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        payload = error.read()
        try:
            return error.code, json.loads(payload or b"null")
        except json.JSONDecodeError:
            return error.code, payload.decode(errors="replace")


def login() -> str:
    """Login requires OAuth2 form encoding, not a JSON body."""
    request = urllib.request.Request(
        f"{BASE}/api/v1/auth/login", data=b"username=analyst&password=analyst123", method="POST"
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())["access_token"]


def main() -> None:
    token = login()
    name = "fraud_classifier"
    results: dict[str, object] = {}

    status, state = call("GET", f"/api/v1/models/{name}/response-state", token=token)
    results["01_response_state"] = {"status": status, "body": state}

    status, reset = call("POST", f"/api/v1/models/{name}/unfreeze", {"reason": "reset before check"}, token=token)
    results["02_unfreeze_reset"] = {"status": status, "body": reset}

    status, frozen = call("POST", f"/api/v1/models/{name}/freeze", {"reason": "verification freeze"}, token=token)
    results["03_freeze"] = {"status": status, "body": frozen}

    status, conflict_body = call("POST", f"/api/v1/models/{name}/freeze", {"reason": "should conflict"}, token=token)
    conflict_status = status
    results["04_double_freeze"] = {"status": conflict_status, "body": conflict_body}

    status, _ = call("GET", f"/api/v1/models/{name}/response-state")
    results["05_anonymous_state_status"] = status

    status, rollback = call("POST", f"/api/v1/models/{name}/rollback", {"reason": "verification rollback"}, token=token)
    results["06_rollback"] = {"status": status, "body": rollback}

    status, audit = call("GET", "/api/v1/audit?limit=200", token=token)
    actions = [
        item["action"]
        for item in (audit or [])
        if item.get("action") in {"model.freeze", "model.unfreeze", "model.rollback"}
    ]
    results["07_audit_actions"] = {"status": status, "count": len(actions), "actions": actions[:10]}

    results["freeze_endpoint_exists"] = status_ok(frozen) and frozen.get("state") == "frozen"
    results["rollback_endpoint_exists"] = status_ok(rollback) and isinstance(rollback.get("current_version"), str)
    results["double_freeze_returns_409"] = conflict_status == 409
    results["anonymous_rejected"] = results["05_anonymous_state_status"] in (401, 403)
    results["audit_events_written"] = set(actions) >= {"model.freeze", "model.rollback"}

    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


def status_ok(body: object) -> bool:
    return isinstance(body, dict) and "state" in body


if __name__ == "__main__":
    main()