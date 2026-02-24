import json
import os

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STATUS_TABLE"])


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    receiving_fein = body.get("receivingFein")  # Required: partition key
    releasing_fein = body.get("releasingFein")  # Required
    carrier_id     = body.get("carrierId")      # Required: sort key
    status         = body.get("status")         # Required
    npn            = body.get("npn")            # Required: agent National Producer Number

    missing = [f for f, v in {
        "receivingFein": receiving_fein,
        "releasingFein": releasing_fein,
        "carrierId":     carrier_id,
        "status":        status,
        "npn":           npn,
    }.items() if not v]

    if missing:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps({
                "error": {
                    "code": "MISSING_FIELDS",
                    "message": f"Missing required fields: {', '.join(missing)}",
                }
            }),
        }

    table.put_item(Item={
        "ReceivingFein": receiving_fein,
        "ReleasingFein": releasing_fein,
        "carrierId":     carrier_id,
        "status":        status,
        "npn":           npn,
    })

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps({
            "receivingFein": receiving_fein,
            "releasingFein": releasing_fein,
            "carrierId":     carrier_id,
            "status":        status,
            "npn":           npn,
        }),
    }
