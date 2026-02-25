import json
import logging
import os
import urllib.request

import boto3

from status import Status

logger = logging.getLogger()
logger.setLevel(logging.INFO)

UPDATE_CONTRACTS_FEIN_URL = os.environ.get("UPDATE_CONTRACTS_FEIN_URL")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STATUS_TABLE"])

VALID_STATUSES = {s.name for s in Status}


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    receiving_fein = body.get("receivingFein")  # Required: partition key
    releasing_fein = body.get("releasingFein")  # Required
    carrier_id = body.get("carrierId")  # Required: sort key
    status = body.get("status")  # Required
    npn = body.get("npn")  # Required: agent National Producer Number
    requirements = body.get("requirements")  # Optional: list of {code, status, details}

    logger.info(
        "set_status called receivingFein=%s releasingFein=%s carrierId=%s status=%s npn=%s",
        receiving_fein, releasing_fein, carrier_id, status, npn,
    )

    missing = [
        f
        for f, v in {
            "receivingFein": receiving_fein,
            "releasingFein": releasing_fein,
            "carrierId": carrier_id,
            "status": status,
            "npn": npn,
        }.items()
        if not v
    ]

    if missing:
        logger.error("Missing required fields: %s", missing)
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps(
                {
                    "error": {
                        "code": "MISSING_FIELDS",
                        "message": f"Missing required fields: {', '.join(missing)}",
                    }
                }
            ),
        }

    if status not in VALID_STATUSES:
        logger.error("Invalid status '%s'. Valid statuses: %s", status, sorted(VALID_STATUSES))
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps(
                {
                    "error": {
                        "code": "INVALID_STATUS",
                        "message": f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
                    }
                }
            ),
        }

    status_key = f"{carrier_id}#{npn}#{releasing_fein}"

    item = {
        "receivingFein": receiving_fein,
        "statusKey": status_key,
        "releasingFein": releasing_fein,
        "carrierId": carrier_id,
        "status": status,
        "npn": npn,
    }
    if requirements is not None:
        item["requirements"] = requirements

    logger.info("Writing status to DynamoDB statusKey=%s", status_key)
    table.put_item(Item=item)
    logger.info("Status written successfully")

    if status == "COMPLETED" and UPDATE_CONTRACTS_FEIN_URL:
        logger.info("Status is COMPLETED, calling update_contracts_fein url=%s", UPDATE_CONTRACTS_FEIN_URL)
        payload = json.dumps({
            "carrierId": carrier_id,
            "npn": npn,
            "releasingFein": releasing_fein,
            "receivingFein": receiving_fein,
        }).encode("utf-8")
        req = urllib.request.Request(
            UPDATE_CONTRACTS_FEIN_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req)
            logger.info("update_contracts_fein called successfully")
        except Exception as e:
            logger.error("update_contracts_fein failed: %s", str(e))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(
            {
                "receivingFein": receiving_fein,
                "releasingFein": releasing_fein,
                "carrierId": carrier_id,
                "status": status,
                "npn": npn,
                "requirements": requirements,
            }
        ),
    }
