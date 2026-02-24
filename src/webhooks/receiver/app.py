import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env", override=False)

app = FastAPI(title="ATS Webhook Receiver")

DE_DUP_TTL_SECONDS = 24 * 60 * 60
_seen_events: dict[str, float] = {}
_dynamodb_resource: Any = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/hooks/ats-status")
async def receive_status_update(
    request: Request,
    x_ats_signature: Optional[str] = Header(default=None, alias="X-ATS-Signature"),
    x_ats_event_id: Optional[str] = Header(default=None, alias="X-ATS-Event-Id"),
) -> dict[str, str]:
    secret = os.getenv("ATS_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Receiver is not configured.")

    if not x_ats_signature:
        raise HTTPException(status_code=401, detail="Missing X-ATS-Signature.")

    if not x_ats_event_id:
        raise HTTPException(status_code=400, detail="Missing X-ATS-Event-Id header.")

    body_bytes = await request.body()

    provided_signature = normalize_signature(x_ats_signature)
    expected_signature = compute_hmac_sha256_hex(body_bytes, secret)

    if not secure_compare_hex(provided_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature.")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc

    validate_payload(payload, x_ats_event_id)

    if not try_register_event(x_ats_event_id):
        return {"status": "duplicate_ignored", "eventId": x_ats_event_id}

    try:
        persist_status_update(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"status": "processed", "eventId": x_ats_event_id}


def compute_hmac_sha256_hex(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def normalize_signature(signature: str) -> str:
    prefix = "sha256="
    if signature.lower().startswith(prefix):
        return signature[len(prefix) :].strip().lower()
    return signature.strip().lower()


def secure_compare_hex(left_hex: str, right_hex: str) -> bool:
    try:
        left = bytes.fromhex(left_hex)
        right = bytes.fromhex(right_hex)
    except ValueError:
        return False
    return hmac.compare_digest(left, right)


def validate_payload(payload: dict[str, Any], event_id_header: str) -> None:
    event_type = payload.get("eventType")
    if event_type != "transfer.status.updated":
        raise HTTPException(status_code=400, detail="Unsupported eventType.")

    payload_event_id = payload.get("eventId")
    if payload_event_id != event_id_header:
        raise HTTPException(
            status_code=400, detail="Header event id does not match payload eventId."
        )

    data = payload.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Payload data must be an object.")

    if not data.get("transferId"):
        raise HTTPException(status_code=400, detail="Payload data.transferId is required.")

    if not data.get("state"):
        raise HTTPException(status_code=400, detail="Payload data.state is required.")


def try_register_event(event_id: str) -> bool:
    now = time.time()
    cleanup_expired_events(now)
    if event_id in _seen_events:
        return False
    _seen_events[event_id] = now + DE_DUP_TTL_SECONDS
    return True


def cleanup_expired_events(now: float) -> None:
    expired = [key for key, expires_at in _seen_events.items() if expires_at <= now]
    for key in expired:
        _seen_events.pop(key, None)


def persist_status_update(payload: dict[str, Any]) -> None:
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    if not table_name:
        return

    partition_key_name = os.getenv("DYNAMODB_PK_NAME", "transferId")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Payload data must be an object.")

    transfer_id = data.get("transferId")
    if not isinstance(transfer_id, str) or not transfer_id.strip():
        raise RuntimeError("Payload data.transferId is required for DynamoDB updates.")

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    table = get_dynamodb_resource().Table(table_name)

    try:
        table.update_item(
            Key={partition_key_name: transfer_id},
            UpdateExpression=(
                "SET #eventId=:eventId, #eventType=:eventType, #occurredAt=:occurredAt, "
                "#source=:source, #transferId=:transferId, #previousState=:previousState, "
                "#state=:state, #reasonCodes=:reasonCodes, #npn=:npn, "
                "#statusMessage=:statusMessage, #effectiveDate=:effectiveDate, #updatedAt=:updatedAt"
            ),
            ExpressionAttributeNames={
                "#eventId": "eventId",
                "#eventType": "eventType",
                "#occurredAt": "occurredAt",
                "#source": "source",
                "#transferId": "transferId",
                "#previousState": "previousState",
                "#state": "state",
                "#reasonCodes": "reasonCodes",
                "#npn": "npn",
                "#statusMessage": "statusMessage",
                "#effectiveDate": "effectiveDate",
                "#updatedAt": "updatedAt",
            },
            ExpressionAttributeValues={
                ":eventId": payload.get("eventId"),
                ":eventType": payload.get("eventType"),
                ":occurredAt": payload.get("occurredAt"),
                ":source": payload.get("source"),
                ":transferId": transfer_id,
                ":previousState": data.get("previousState"),
                ":state": data.get("state"),
                ":reasonCodes": data.get("reasonCodes") or [],
                ":npn": data.get("npn"),
                ":statusMessage": data.get("statusMessage"),
                ":effectiveDate": data.get("effectiveDate"),
                ":updatedAt": now,
            },
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("Failed to update DynamoDB record.") from exc


def get_dynamodb_resource() -> Any:
    global _dynamodb_resource
    if _dynamodb_resource is None:
        resource_config: dict[str, str] = {}
        region = os.getenv("AWS_REGION")
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")

        if region:
            resource_config["region_name"] = region
        if endpoint_url:
            resource_config["endpoint_url"] = endpoint_url

        _dynamodb_resource = boto3.resource("dynamodb", **resource_config)
    return _dynamodb_resource
