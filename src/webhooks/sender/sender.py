import hashlib
import hmac
import importlib
import json
import os
import sys
import time
import uuid
from typing import Any, Optional, Set
from urllib.parse import urlparse, urlunparse

import requests

ALLOWED_STATES: Set[str] = {
    "SUBMITTED",
    "VALIDATION",
    "PROCESSING",
    "COMPLETED",
    "REJECTED",
    "WITHDRAWN",
}


def main() -> int:
    webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:8000/hooks/ats-status")
    secret = os.getenv("ATS_WEBHOOK_SECRET", "local-dev-shared-secret")
    delay_ms = parse_int(os.getenv("SENDER_DELAY_MS"), 0)
    auto_send = is_enabled(os.getenv("SENDER_AUTO_SEND"))
    aws_sign_request = is_enabled(os.getenv("AWS_SIGN_REQUEST"))
    aws_region = os.getenv("AWS_REGION") or infer_region_from_url(webhook_url)
    aws_service = os.getenv("AWS_SIGV4_SERVICE", "lambda")

    payload_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "src/webhooks/receiver/examples/payload.json"
    )

    if delay_ms > 0:
        print(f"Delaying send by {delay_ms}ms...")
        time.sleep(delay_ms / 1000)

    if not os.path.exists(payload_path):
        print(f"Payload file not found: {payload_path}", file=sys.stderr)
        return 1

    with open(payload_path, "r", encoding="utf-8") as file:
        template_payload = json.load(file)

    if not isinstance(template_payload, dict):
        raise RuntimeError("Payload must be a JSON object.")

    data = template_payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Payload must include a data object.")

    current_state = data.get("state")
    if not isinstance(current_state, str) or not current_state.strip():
        raise RuntimeError("Payload data.state must be provided.")

    current_state = current_state.strip().upper()
    warn_if_endpoint_looks_wrong(webhook_url)

    while True:
        next_state = read_required_state("Enter transfer status to send", ALLOWED_STATES)
        event_id = f"evt_{uuid.uuid4().hex}"

        payload = build_payload_for_status_update(
            template_payload, event_id, current_state, next_state
        )
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = compute_hmac_sha256_hex(payload_bytes, secret)

        print(f"Sending to: {webhook_url}")
        print(f"Payload: {payload_path}")
        print(f"EventId: {event_id}")
        print(f"PreviousState: {current_state}")
        print(f"State: {next_state}")

        request_headers = build_headers(
            base_headers={
                "X-ATS-Event-Id": event_id,
                "X-ATS-Signature": f"sha256={signature}",
                "Content-Type": "application/json",
            },
            aws_sign_request=aws_sign_request,
            aws_region=aws_region,
            aws_service=aws_service,
            body=payload_bytes,
            url=webhook_url,
            method="POST",
            secret_hint=secret,
        )

        response = requests.post(
            webhook_url,
            data=payload_bytes,
            headers=request_headers,
            timeout=30,
        )

        print(f"Request Status: {response.status_code} {response.reason}")
        if response.text.strip():
            print("Response:")
            print(response.text)

        if response.status_code == 403:
            print("Hint: 403 is typically infrastructure/auth, not webhook payload validation.")
            print("- Verify endpoint URL/path is correct.")
            print("- For IAM-protected endpoints set AWS_SIGN_REQUEST=true and AWS_REGION.")
            print("- For Lambda Function URL with auth NONE, disable AWS_SIGN_REQUEST.")

        current_state = next_state


def build_payload_for_status_update(
    template_payload: dict[str, Any], event_id: str, previous_state: str, state: str
) -> dict[str, Any]:
    payload = json.loads(json.dumps(template_payload))

    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Payload must include a data object.")

    payload["eventId"] = event_id
    payload["occurredAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data["previousState"] = previous_state
    data["state"] = state

    return payload


def read_required_state(prompt: str, allowed_states: Set[str]) -> str:
    values = ", ".join(sorted(allowed_states))
    while True:
        user_input = input(f"{prompt} [{values}]: ").strip().upper()
        if not user_input:
            print("Status is required.")
            continue
        if user_input in allowed_states:
            return user_input
        print("Invalid status. Please enter one of the allowed values.")


def compute_hmac_sha256_hex(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def is_enabled(raw: Optional[str]) -> bool:
    if not raw:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def parse_int(raw: Optional[str], fallback: int) -> int:
    if not raw:
        return fallback
    try:
        return int(raw)
    except ValueError:
        return fallback


def infer_region_from_url(url: str) -> Optional[str]:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return None

    parts = host.split(".")
    for i, part in enumerate(parts):
        if part == "amazonaws" and i > 0:
            candidate = parts[i - 1]
            if "-" in candidate and any(ch.isdigit() for ch in candidate):
                return candidate
    return None


def warn_if_endpoint_looks_wrong(webhook_url: str) -> None:
    parsed = urlparse(webhook_url)
    host = (parsed.hostname or "").lower()
    is_local = host in {"localhost", "127.0.0.1", "::1"}

    if not is_local:
        return

    probe_url = urlunparse((parsed.scheme, parsed.netloc, "/health", "", "", ""))

    try:
        response = requests.get(probe_url, timeout=2)
    except requests.RequestException:
        return

    server_header = (response.headers.get("server") or "").lower()
    body_preview = response.text[:200].lower() if response.text else ""

    if "airtunes" in server_header or "airplay" in body_preview:
        print("Warning: target appears to be macOS AirTunes/ControlCenter, not the webhook receiver.")
        print(f"- WEBHOOK_URL: {webhook_url}")
        print(f"- Probe endpoint: {probe_url} returned {response.status_code} {response.reason}")
        print("- Use receiver on port 8000, or update WEBHOOK_URL to the correct endpoint.")


def build_headers(
    base_headers: dict[str, str],
    aws_sign_request: bool,
    aws_region: Optional[str],
    aws_service: str,
    body: bytes,
    url: str,
    method: str,
    secret_hint: str,
) -> dict[str, str]:
    headers = dict(base_headers)

    if not aws_sign_request:
        return headers

    try:
        sigv4_auth = importlib.import_module("botocore.auth").SigV4Auth
        aws_request_type = importlib.import_module("botocore.awsrequest").AWSRequest
        session_type = importlib.import_module("botocore.session").Session
    except ImportError as exc:
        raise RuntimeError(
            "AWS_SIGN_REQUEST=true requires botocore. Install with: pip install botocore"
        ) from exc

    if not aws_region:
        raise RuntimeError(
            "AWS_SIGN_REQUEST=true requires AWS_REGION (or a parseable AWS URL)."
        )

    session = session_type()
    credentials = session.get_credentials()
    if credentials is None:
        raise RuntimeError("AWS credentials not found for SigV4 signing.")

    frozen = credentials.get_frozen_credentials()
    aws_request = aws_request_type(method=method, url=url, data=body, headers=headers)
    sigv4_auth(frozen, aws_service, aws_region).add_auth(aws_request)

    signed_headers = {str(k): str(v) for k, v in aws_request.headers.items()}
    signed_headers["X-ATS-Signature"] = base_headers["X-ATS-Signature"]
    signed_headers["X-ATS-Event-Id"] = base_headers["X-ATS-Event-Id"]
    signed_headers["Content-Type"] = base_headers["Content-Type"]

    print(f"SigV4 signing enabled (service={aws_service}, region={aws_region}).")
    print(f"Webhook shared-secret length: {len(secret_hint)}")

    return signed_headers


if __name__ == "__main__":
    raise SystemExit(main())
