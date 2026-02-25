import json
import os

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TRANSFERS_TABLE"])


def lambda_handler(event, context):
    releasing_fein = (event.get("pathParameters") or {}).get("id")

    if not releasing_fein:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps({"error": {"code": "MISSING_FEIN", "message": "releasing FEIN is required"}}),
        }

    result = table.scan(FilterExpression=Attr("releasingImoFein").eq(releasing_fein))
    items = result.get("Items", [])

    # Handle DynamoDB pagination
    while "LastEvaluatedKey" in result:
        result = table.scan(
            FilterExpression=Attr("releasingImoFein").eq(releasing_fein),
            ExclusiveStartKey=result["LastEvaluatedKey"],
        )
        items.extend(result.get("Items", []))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(items),
    }
