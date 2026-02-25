import json
import os

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CONTRACTS_TABLE"])


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
            "body": json.dumps(
                {"error": {"code": "MISSING_FEIN", "message": "fein path parameter is required"}}
            ),
        }

    response = table.scan(FilterExpression=Attr("fein").eq(fein))
    items = response["Items"]

    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Attr("fein").eq(fein),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response["Items"])

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(items),
    }
