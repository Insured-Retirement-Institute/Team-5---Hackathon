import hashlib
import hmac
import importlib.util
import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

WEBHOOKS_DIR = Path(__file__).resolve().parents[1]
RECEIVER_DIR = WEBHOOKS_DIR / "receiver"
sys.path.insert(0, str(RECEIVER_DIR))

spec = importlib.util.spec_from_file_location("receiver_app", RECEIVER_DIR / "app.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load receiver app module for tests.")
receiver_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver_app)


def compute_signature(payload: dict, secret: str) -> str:
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def build_payload(event_id: str) -> dict:
    return {
        "eventId": event_id,
        "eventType": "transfer.status.updated",
        "occurredAt": "2026-02-24T20:09:12Z",
        "source": "centralized-hub",
        "data": {
            "transferId": "tr_abc123",
            "previousState": "VALIDATION",
            "state": "PROCESSING",
            "reasonCodes": ["ALL_REQUIREMENTS_SATISFIED"],
            "npn": "17439285",
        },
    }


def test_valid_signature_processed(monkeypatch):
    monkeypatch.setenv("ATS_WEBHOOK_SECRET", "integration-test-shared-secret")
    receiver_app._seen_events.clear()
    client = TestClient(receiver_app.app)

    event_id = "evt_valid_001"
    payload = build_payload(event_id)
    signature = compute_signature(payload, "integration-test-shared-secret")

    response = client.post(
        "/hooks/ats-status",
        json=payload,
        headers={
            "X-ATS-Event-Id": event_id,
            "X-ATS-Signature": f"sha256={signature}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_invalid_signature_unauthorized(monkeypatch):
    monkeypatch.setenv("ATS_WEBHOOK_SECRET", "integration-test-shared-secret")
    receiver_app._seen_events.clear()
    client = TestClient(receiver_app.app)

    event_id = "evt_invalid_sig"
    payload = build_payload(event_id)

    response = client.post(
        "/hooks/ats-status",
        json=payload,
        headers={
            "X-ATS-Event-Id": event_id,
            "X-ATS-Signature": "sha256=deadbeef",
        },
    )

    assert response.status_code == 401


def test_duplicate_event_ignored(monkeypatch):
    monkeypatch.setenv("ATS_WEBHOOK_SECRET", "integration-test-shared-secret")
    receiver_app._seen_events.clear()
    client = TestClient(receiver_app.app)

    event_id = "evt_duplicate_001"
    payload = build_payload(event_id)
    signature = compute_signature(payload, "integration-test-shared-secret")
    headers = {
        "X-ATS-Event-Id": event_id,
        "X-ATS-Signature": f"sha256={signature}",
    }

    first_response = client.post("/hooks/ats-status", json=payload, headers=headers)
    second_response = client.post("/hooks/ats-status", json=payload, headers=headers)

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "processed"
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "duplicate_ignored"


def test_dynamodb_update_called_once_for_duplicate_event(monkeypatch):
    monkeypatch.setenv("ATS_WEBHOOK_SECRET", "integration-test-shared-secret")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "transfers")
    monkeypatch.setenv("DYNAMODB_PK_NAME", "transferId")
    receiver_app._seen_events.clear()

    class FakeTable:
        def __init__(self):
            self.calls = 0

        def update_item(self, **kwargs):
            self.calls += 1
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    class FakeDynamoResource:
        def __init__(self, table):
            self._table = table

        def Table(self, table_name):
            assert table_name == "transfers"
            return self._table

    fake_table = FakeTable()
    monkeypatch.setattr(
        receiver_app,
        "get_dynamodb_resource",
        lambda: FakeDynamoResource(fake_table),
    )

    client = TestClient(receiver_app.app)
    event_id = "evt_ddb_duplicate_001"
    payload = build_payload(event_id)
    signature = compute_signature(payload, "integration-test-shared-secret")
    headers = {
        "X-ATS-Event-Id": event_id,
        "X-ATS-Signature": f"sha256={signature}",
    }

    first_response = client.post("/hooks/ats-status", json=payload, headers=headers)
    second_response = client.post("/hooks/ats-status", json=payload, headers=headers)

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "processed"
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "duplicate_ignored"
    assert fake_table.calls == 1
