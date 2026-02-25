import json
import os

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CONTRACTS_TABLE"])


def update_contracts_fein(carrier_id, npn, receiving_fein, releasing_fein):
    # Scan for contracts matching carrierId, npn, and releasingFein
    response = table.scan(
        FilterExpression=(
            Attr("carrierId").eq(carrier_id)
            & Attr("npn").eq(npn)
            & Attr("fein").eq(releasing_fein)
        )
    )

    items = response["Items"]

    # Handle pagination in case there are more results
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=(
                Attr("carrierId").eq(carrier_id)
                & Attr("npn").eq(npn)
                & Attr("fein").eq(releasing_fein)
            ),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response["Items"])

    # Update each matching contract's fein to the receiving fein
    for item in items:
        table.update_item(
            Key={"id": item["id"]},
            UpdateExpression="SET fein = :new_fein",
            ExpressionAttributeValues={":new_fein": receiving_fein},
        )

    return len(items)


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    carrier_id = body.get("carrierId")
    npn = body.get("npn")
    receiving_fein = body.get("receivingFein")
    releasing_fein = body.get("releasingFein")

    missing = [
        f
        for f, v in {
            "carrierId": carrier_id,
            "npn": npn,
            "receivingFein": receiving_fein,
            "releasingFein": releasing_fein,
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

    updated_count = update_contracts_fein(carrier_id, npn, receiving_fein, releasing_fein)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps({"updatedCount": updated_count}),
    }
