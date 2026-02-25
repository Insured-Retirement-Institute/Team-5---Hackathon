import json
import os

import boto3

from status import Status

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

    table.put_item(Item=item)

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
