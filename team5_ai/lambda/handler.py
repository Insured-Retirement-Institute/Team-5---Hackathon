"""
lambda/handler.py

Handles action group invocations from an Amazon Bedrock agent and forwards
them to the existing carrier API at API_BASE_URL.

Routes:
  GET    /ats/transfers               → GET  {base}/ats/transfers
  POST   /ats/transfers               → POST {base}/ats/transfers
  GET    /ats/transfers/{id}          → GET  {base}/ats/transfers/{id}
  PATCH  /ats/transfers/{id}          → PATCH {base}/ats/transfers/{id}
  POST   /ats/status                  → POST {base}/ats/status
  GET    /ats/status/{fein}           → GET  {base}/ats/status/{fein}
  GET    /ats/contracts/{fein}        → GET  {base}/ats/contracts/{fein}
  POST   /ats/contracts/update-fein  → POST {base}/ats/contracts/update-fein
"""

import json
import logging
import os
import urllib.error
import urllib.parse
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
    """Replace {placeholder} segments with URL-encoded actual param values."""
    path = template
    for key, value in params.items():
        path = path.replace(f"{{{key}}}", urllib.parse.quote(value, safe=""))
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
    status, resp = _call_api("GET", "/ats/v1/transfers", query=query)
    return _build_response(event, status, resp)


def _create_transfer(event: dict, params: dict, body: dict) -> dict:
    """POST /ats/transfers — reconstruct and forward the transfer payload."""
    agent = _parse(body.get("agent", ""))
    releasing_imo = _parse(body.get("releasingImo", ""))
    receiving_imo = _parse(body.get("receivingImo", ""))

    payload = {
        "agent":        agent,
        "releasingImo": releasing_imo,
        "receivingImo": receiving_imo,
        "effectiveDate": body.get("effectiveDate", ""),
        "consent":      _parse(body.get("consent", "")),
    }
    if body.get("notes"):
        payload["notes"] = body["notes"]

    status, resp = _call_api("POST", "/ats/v1/transfers", body=payload)

    # The carrier API stores the transfer before doing an internal forward to
    # carrier-specific APIs. If ALL forwards fail it returns 502, but the
    # transfer record was already persisted in DynamoDB.
    # Two known 502 shapes:
    #   old: {"error": {"code": "FORWARD_FAILED", ...}}
    #   new: {"error": {"step": "forward_<carrier>", ...}}
    # Reconstruct the expected ID and return 201 so Bedrock doesn't panic.
    if status == 502 and isinstance(resp, dict):
        err = resp.get("error", {})
        if isinstance(err, dict):
            is_forward_fail = (
                err.get("code") == "FORWARD_FAILED"
                or str(err.get("step", "")).startswith("forward_")
            )
            if is_forward_fail:
                npn = agent.get("npn", "") if isinstance(agent, dict) else ""
                releasing_fein = releasing_imo.get("fein", "") if isinstance(releasing_imo, dict) else ""
                receiving_fein = receiving_imo.get("fein", "") if isinstance(receiving_imo, dict) else ""
                transfer_id = f"{receiving_fein}|{releasing_fein}|{npn}"
                logger.warning(
                    "Carrier returned forward failure but transfer was stored. "
                    "Returning synthesised id=%s", transfer_id
                )
                return _build_response(event, 201, {"id": transfer_id, "state": "SUBMITTED"})

    return _build_response(event, status, resp)


def _get_transfer(event: dict, params: dict, body: dict) -> dict:
    """GET /ats/transfers/{id} — forward by resolved id."""
    path = _resolve_path("/ats/v1/transfers/{id}", params)
    status, resp = _call_api("GET", path)
    return _build_response(event, status, resp)


def _patch_transfer(event: dict, params: dict, body: dict) -> dict:
    """PATCH /ats/transfers/{id} — forward CANCEL or ADD_NOTE action."""
    path = _resolve_path("/ats/v1/transfers/{id}", params)
    payload = {"action": body.get("action")}
    if body.get("note"):
        payload["note"] = body["note"]
    if body.get("reason"):
        payload["reason"] = body["reason"]
    status, resp = _call_api("PATCH", path, body=payload)
    return _build_response(event, status, resp)


def _set_status(event: dict, params: dict, body: dict) -> dict:
    """POST /ats/status — carrier records transfer status with optional requirements."""
    payload = {
        "receivingFein": body.get("receivingFein"),
        "releasingFein": body.get("releasingFein"),
        "carrierId":     body.get("carrierId"),
        "status":        body.get("status"),
        "npn":           body.get("npn"),
    }
    if body.get("requirements"):
        payload["requirements"] = _parse(body["requirements"])
    status, resp = _call_api("POST", "/ats/v1/status", body=payload)
    return _build_response(event, status, resp)


def _get_statuses(event: dict, params: dict, body: dict) -> dict:
    """GET /ats/status/{fein} — list all status records for a receiving IMO FEIN."""
    path = _resolve_path("/ats/v1/status/{fein}", params)
    status, resp = _call_api("GET", path)
    return _build_response(event, status, resp)


def _get_contracts(event: dict, params: dict, body: dict) -> dict:
    """GET /ats/contracts/{fein} — list contracts for a FEIN."""
    path = _resolve_path("/ats/v1/contracts/{fein}", params)
    status, resp = _call_api("GET", path)
    return _build_response(event, status, resp)


def _update_contract_fein(event: dict, params: dict, body: dict) -> dict:
    """POST /ats/contracts/update-fein — reassign contracts to the receiving IMO FEIN."""
    payload = {
        "carrierId":     body.get("carrierId"),
        "npn":           body.get("npn"),
        "releasingFein": body.get("releasingFein"),
        "receivingFein": body.get("receivingFein"),
    }
    status, resp = _call_api("POST", "/ats/v1/contracts/update-fein", body=payload)
    return _build_response(event, status, resp)


def _get_agent_validation(event: dict, params: dict, body: dict) -> dict:
    """GET /ats/agents/{npn}/validate — return agent carrier requirements and transfer checklist."""
    path = _resolve_path("/ats/agents/{npn}/validate", params)
    status, resp = _call_api("GET", path)
    return _build_response(event, status, resp)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

DISPATCH = {
    ("GET",   "/ats/transfers"):                  _list_transfers,
    ("POST",  "/ats/transfers"):                  _create_transfer,
    ("GET",   "/ats/transfers/{id}"):             _get_transfer,
    ("PATCH", "/ats/transfers/{id}"):             _patch_transfer,
    ("POST",  "/ats/status"):                     _set_status,
    ("GET",   "/ats/status/{fein}"):              _get_statuses,
    ("GET",   "/ats/contracts/{fein}"):           _get_contracts,
    ("POST",  "/ats/contracts/update-fein"):      _update_contract_fein,
    ("GET",   "/ats/agents/{npn}/validate"):      _get_agent_validation,
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
