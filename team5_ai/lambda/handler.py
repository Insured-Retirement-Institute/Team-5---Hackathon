"""
lambda/handler.py

Handles action group invocations from an Amazon Bedrock agent and forwards
them to the existing carrier API at API_BASE_URL.

Routes:
  GET    /ats/transfers          → GET  {base}/ats/transfers
  POST   /ats/transfers          → POST {base}/ats/transfers
  GET    /ats/transfers/{id}     → GET  {base}/ats/transfers/{id}
  PATCH  /ats/transfers/{id}     → PATCH {base}/ats/transfers/{id}
"""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

API_BASE_URL = os.environ["API_BASE_URL"].rstrip("/")


# ---------------------------------------------------------------------------
# Bedrock event helpers
# ---------------------------------------------------------------------------

def _params(event: dict) -> dict:
    """Path + query parameters as a flat dict."""
    return {p["name"]: p["value"] for p in event.get("parameters", []) or []}


def _body(event: dict) -> dict:
    """Request body properties as a flat dict (values still raw strings)."""
    try:
        props = event["requestBody"]["content"]["application/json"]["properties"]
        return {p["name"]: p["value"] for p in props}
    except (KeyError, TypeError):
        return {}


def _parse(value):
    """
    Parse a value that may be:
      - standard JSON string   e.g. '{"npn":"12345"}'
      - Bedrock {key=value}    e.g. '{npn=12345, name=Brett}'
      - plain scalar string
    """
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass
    if stripped.startswith("{") and stripped.endswith("}"):
        inner = stripped[1:-1]
        result = {}
        for part in inner.split(", "):
            if "=" in part:
                key, _, val = part.partition("=")
                if key.strip():  # skip entries where model omitted the key name
                    result[key.strip()] = _coerce(val.strip())
        return result
    return value


def _coerce(value: str):
    """Convert 'true'/'false' strings to booleans; leave everything else alone."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def _resolve_path(template: str, params: dict) -> str:
    """Replace {placeholder} segments with actual param values."""
    path = template
    for key, value in params.items():
        path = path.replace(f"{{{key}}}", value)
    return path


# ---------------------------------------------------------------------------
# Bedrock response helpers
# ---------------------------------------------------------------------------

def _build_response(event: dict, status_code: int, body) -> dict:
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "apiPath": event["apiPath"],
            "httpMethod": event["httpMethod"],
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            },
        },
        "sessionAttributes": event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {}),
    }


def _error(event: dict, status_code: int, code: str, message: str) -> dict:
    return _build_response(event, status_code, {"error": {"code": code, "message": message}})


# ---------------------------------------------------------------------------
# HTTP forwarding
# ---------------------------------------------------------------------------

def _call_api(method: str, path: str, query: dict = None, body: dict = None):
    """
    Call the carrier API and return (http_status_code, parsed_response_body).
    """
    url = API_BASE_URL + path
    if query:
        qs = "&".join(f"{k}={v}" for k, v in query.items() if v is not None)
        if qs:
            url += "?" + qs

    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    logger.info("Calling %s %s body=%s", method, url, json.dumps(body) if body else None)

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            logger.info("Response %s: %s", resp.status, raw[:500])
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"body": raw}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        logger.warning("HTTP error %s: %s", exc.code, raw[:500])
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _list_transfers(event: dict, params: dict, body: dict) -> dict:
    """GET /ats/transfers — forward with optional npn/state/limit filters."""
    query = {k: params[k] for k in ("npn", "state", "limit") if k in params}
    status, resp = _call_api("GET", "/ats/transfers", query=query)
    return _build_response(event, status, resp)


def _create_transfer(event: dict, params: dict, body: dict) -> dict:
    """POST /ats/transfers — reconstruct and forward the transfer payload."""
    payload = {
        "agent":        _parse(body.get("agent", "")),
        "releasingImo": _parse(body.get("releasingImo", "")),
        "receivingImo": _parse(body.get("receivingImo", "")),
        "effectiveDate": body.get("effectiveDate", ""),
        "consent":      _parse(body.get("consent", "")),
    }
    if body.get("notes"):
        payload["notes"] = body["notes"]

    status, resp = _call_api("POST", "/ats/transfers", body=payload)
    return _build_response(event, status, resp)


def _get_transfer(event: dict, params: dict, body: dict) -> dict:
    """GET /ats/transfers/{id} — forward by resolved id."""
    path = _resolve_path("/ats/transfers/{id}", params)
    status, resp = _call_api("GET", path)
    return _build_response(event, status, resp)


def _patch_transfer(event: dict, params: dict, body: dict) -> dict:
    """PATCH /ats/transfers/{id} — forward CANCEL or ADD_NOTE action."""
    path = _resolve_path("/ats/transfers/{id}", params)
    payload = {"action": body.get("action")}
    if body.get("note"):
        payload["note"] = body["note"]
    if body.get("reason"):
        payload["reason"] = body["reason"]
    status, resp = _call_api("PATCH", path, body=payload)
    return _build_response(event, status, resp)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

DISPATCH = {
    ("GET",   "/ats/transfers"):       _list_transfers,
    ("POST",  "/ats/transfers"):       _create_transfer,
    ("GET",   "/ats/transfers/{id}"): _get_transfer,
    ("PATCH", "/ats/transfers/{id}"): _patch_transfer,
}


def _dispatch(event: dict) -> dict:
    method = event.get("httpMethod", "").upper()
    api_path = event.get("apiPath", "")
    logger.info("Dispatching %s %s (actionGroup=%s)", method, api_path, event.get("actionGroup"))

    handler_fn = DISPATCH.get((method, api_path))
    if handler_fn is None:
        return _error(event, 404, "NOT_FOUND", f"No handler for {method} {api_path}")

    try:
        return handler_fn(event, _params(event), _body(event))
    except Exception as exc:
        logger.exception("Unhandled exception: %s", exc)
        return _error(event, 500, "INTERNAL_ERROR", "Internal server error")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event: dict, context) -> dict:
    logger.info("Event: %s", json.dumps(event))
    return _dispatch(event)
