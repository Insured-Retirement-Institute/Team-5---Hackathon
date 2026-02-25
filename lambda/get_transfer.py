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
            "body": json.dumps(
                {
                    "error": {
                        "code": "MISSING_FEIN",
                        "message": "releasing FEIN is required",
                    }
                }
            ),
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

    transfers = [dynamo_record_to_carrier_body(item) for item in items]

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(transfers),
    }


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
        "id": record["id"],
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
