import json
import os

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STATUS_TABLE"])


def lambda_handler(event, context):
    fein = (event.get("pathParameters") or {}).get("fein")

    if not fein:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
            },
            "body": json.dumps({"error": {"code": "MISSING_FEIN", "message": "fein path parameter is required"}}),
        }

    response = table.query(
        KeyConditionExpression=Key("ReceivingFein").eq(fein)
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(response["Items"]),
    }
