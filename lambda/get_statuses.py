import json
import os

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["STATUS_TABLE"])
agent_table = dynamodb.Table(os.environ["AGENT_TABLE"])


def get_agent(npn):
    response = agent_table.get_item(Key={"npn": npn})
    return response.get("Item")


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
                {
                    "error": {
                        "code": "MISSING_FEIN",
                        "message": "fein path parameter is required",
                    }
                }
            ),
        }

    response = table.query(KeyConditionExpression=Key("receivingFein").eq(fein))

    items = []
    for status in response["Items"]:
        npn = status.get("npn")
        agent = get_agent(npn) if npn else None
        items.append(
            {
                **status,
                "agentFirstName": agent.get("firstName") if agent else None,
                "agentLastName": agent.get("lastName") if agent else None,
            }
        )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
        },
        "body": json.dumps(items),
    }
