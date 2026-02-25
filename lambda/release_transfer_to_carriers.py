import json
import logging
import os
import urllib.error
import urllib.request

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TRANSFERS_TABLE"])

FORWARD_API_URL_ALLIANZ = os.environ.get("FORWARD_API_URL_ALLIANZ")
FORWARD_API_URL_AE = os.environ.get("FORWARD_API_URL_AE")

forward_apis = [FORWARD_API_URL_ALLIANZ, FORWARD_API_URL_AE]
carrier_ids = ["allianz", "american-equity"]


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


def dynamo_record_to_carrier_body(record):
    agent = {"npn": record["agentNpn"]}
    if "agentFirstName" in record:
        agent["firstName"] = record["agentFirstName"]
    if "agentLastName" in record:
        agent["lastName"] = record["agentLastName"]

    consent = {"agentAttestation": record.get("agentAttestation", False)}
    if "eSignatureRef" in record:
        consent["eSignatureRef"] = record["eSignatureRef"]

    body = {
        "agent": agent,
        "releasingImo": {
            "fein": record["releasingImoFein"],
            "name": record["releasingImoName"],
        },
        "receivingImo": {
            "fein": record["receivingImoFein"],
            "name": record["receivingImoName"],
        },
        "effectiveDate": record["effectiveDate"],
        "consent": consent,
    }
    if "notes" in record:
        body["notes"] = record["notes"]

    return body


def lambda_handler(event, context):
    transfer_id = (event.get("pathParameters") or {}).get("id")

    if not transfer_id:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps({"error": {"code": "MISSING_ID", "message": "transfer id is required"}}),
        }

    result = table.get_item(Key={"id": transfer_id})
    record = result.get("Item")

    if not record:
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps({"error": {"code": "NOT_FOUND", "message": f"transfer {transfer_id} not found"}}),
        }

    carrier_body = dynamo_record_to_carrier_body(record)

    forward_errors = {}
    for url, carrier_id in zip(forward_apis, carrier_ids):
        logger.info("Releasing transfer=%s to carrier=%s url=%s", transfer_id, carrier_id, url)
        error_status, forward_body = forward_to_api(carrier_body, url)
        if error_status is not None:
            logger.error("Forward failed carrier=%s status=%s body=%s", carrier_id, error_status, forward_body)
            forward_errors[carrier_id] = {"status": error_status, "body": forward_body}

    if len(forward_errors) == len(forward_apis):
        _, first_error = next(iter(forward_errors.items()))
        return {
            "statusCode": first_error["status"],
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": first_error["body"],
        }

    response_body = {"id": transfer_id}
    if forward_errors:
        response_body["warnings"] = {
            cid: f"forward failed — {e['status']}: {e['body']}"
            for cid, e in forward_errors.items()
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(response_body),
    }
