import json
import logging
import os
import traceback
import urllib.error
import urllib.request

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TRANSFERS_TABLE"])
agent_table = dynamodb.Table(os.environ["AGENT_TABLE"])

FORWARD_API_URL_ALLIANZ = os.environ.get("FORWARD_API_URL_ALLIANZ")
FORWARD_API_URL_AE = os.environ.get("FORWARD_API_URL_AE")
SET_STATUS_URL = os.environ.get("SET_STATUS_URL")

forward_apis = [FORWARD_API_URL_ALLIANZ, FORWARD_API_URL_AE]
carrier_ids = ["allianz", "americanEquity"]


def forward_to_api(body, url):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as response:
            return None, response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.status, e.read().decode("utf-8")
    except urllib.error.URLError as e:
        return 502, json.dumps(
            {"error": {"code": "FORWARD_FAILED", "message": str(e.reason)}}
        )


def _error_response(status_code, step, message):
    logger.error("step=%s error=%s", step, message)
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps({"error": {"step": step, "message": message}}),
    }


def lambda_handler(event, context):
    try:
        # Headers
        headers = event.get("headers") or {}
        idempotency_key = headers.get(
            "Idempotency-Key"
        )  # Optional: safely retry POST without creating duplicates

        # Request body
        body = json.loads(event.get("body") or "{}")

        # Agent (required)
        agent = body.get("agent", {})
        agent_npn = agent.get("npn")  # Required: National Producer Number
        agent_first_name = agent.get("firstName")  # Optional
        agent_last_name = agent.get("lastName")  # Optional

        # Releasing IMO (required)
        releasing_imo = body.get("releasingImo", {})
        releasing_imo_fein = releasing_imo.get("fein")  # Required: Business FEIN
        releasing_imo_name = releasing_imo.get("name")  # Required

        # Receiving IMO (required)
        receiving_imo = body.get("receivingImo", {})
        receiving_imo_fein = receiving_imo.get("fein")  # Required: Business FEIN
        receiving_imo_name = receiving_imo.get("name")  # Required

        # Transfer details
        effective_date = body.get(
            "effectiveDate"
        )  # Required: target date for hierarchy/commission realignment (YYYY-MM-DD)

        # Consent (required)
        consent = body.get("consent", {})
        agent_attestation = consent.get(
            "agentAttestation"
        )  # Required: True if agent has authorized this transfer
        e_signature_ref = consent.get(
            "eSignatureRef"
        )  # Optional: reference to e-signature artifact

        # Optional notes
        notes = body.get(
            "notes"
        )  # Optional: free text for carrier processing (max 2000 chars)

        key = f"{receiving_imo_fein}|{releasing_imo_fein}|{agent_npn}"

        item = {
            "id": key,
            "state": "SUBMITTED",
            "agentNpn": agent_npn,
            "agentFirstName": agent_first_name,
            "agentLastName": agent_last_name,
            "releasingImoFein": releasing_imo_fein,
            "releasingImoName": releasing_imo_name,
            "receivingImoFein": receiving_imo_fein,
            "receivingImoName": receiving_imo_name,
            "effectiveDate": effective_date,
            "agentAttestation": agent_attestation,
            "eSignatureRef": e_signature_ref,
            "notes": notes,
            "idempotencyKey": idempotency_key,
        }

        # Remove None values so DynamoDB doesn't reject them
        item = {k: v for k, v in item.items() if v is not None}

        try:
            table.put_item(Item=item)
        except Exception as e:
            return _error_response(500, "dynamo_put_transfer", str(e))

        agent_record = {"npn": agent_npn}
        if agent_first_name:
            agent_record["firstName"] = agent_first_name
        if agent_last_name:
            agent_record["lastName"] = agent_last_name
        try:
            agent_table.put_item(Item=agent_record)
        except Exception as e:
            return _error_response(500, "dynamo_put_agent", str(e))

        forward_errors = {}
        status_warnings = {}
        for url, carrier_id in zip(forward_apis, carrier_ids):
            logger.info("Forwarding transfer to carrier=%s url=%s", carrier_id, url)
            error_status, forward_body = forward_to_api(body, url)
            if error_status is not None:
                logger.error("Forward failed carrier=%s status=%s body=%s", carrier_id, error_status, forward_body)
                forward_errors[carrier_id] = {"status": error_status, "body": forward_body}
                continue

            if SET_STATUS_URL:
                status_payload = json.dumps(
                    {
                        "receivingFein": receiving_imo_fein,
                        "releasingFein": releasing_imo_fein,
                        "carrierId": carrier_id,
                        "status": "INITIATED",
                        "npn": agent_npn,
                    }
                ).encode("utf-8")
                status_req = urllib.request.Request(
                    SET_STATUS_URL,
                    data=status_payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    urllib.request.urlopen(status_req)
                except urllib.error.HTTPError as e:
                    error_body = e.read().decode("utf-8")
                    logger.error("set_status failed carrier=%s status=%s body=%s", carrier_id, e.code, error_body)
                    status_warnings[carrier_id] = {"status": e.code, "message": error_body}
                except Exception as e:
                    logger.error("set_status failed carrier=%s error=%s", carrier_id, str(e))
                    status_warnings[carrier_id] = {"status": 502, "message": str(e)}

        if len(forward_errors) == len(forward_apis):
            first_carrier, first_error = next(iter(forward_errors.items()))
            return _error_response(first_error["status"], f"forward_{first_carrier}", first_error["body"])

        response_body = {"id": key, "state": "SUBMITTED"}
        if status_warnings:
            response_body["warnings"] = {
                carrier_id: f"set_status failed — {w['status']}: {w['message']}"
                for carrier_id, w in status_warnings.items()
            }

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Location": f"/ats/transfers/{key}",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps(response_body),
        }

    except Exception:
        tb = traceback.format_exc()
        logger.error("Unhandled exception: %s", tb)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps({"error": {"step": "unhandled", "message": tb}}),
        }
