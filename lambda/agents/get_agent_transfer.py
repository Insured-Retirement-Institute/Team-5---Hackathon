import json

try:
    from .data import get_agent
except ImportError:
    from data import get_agent


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
}


def lambda_handler(event, context):
    agent_id = (event.get("pathParameters") or {}).get("id")
    if not agent_id:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {
                    "error": {
                        "code": "MISSING_AGENT_ID",
                        "message": "Path parameter 'id' is required.",
                    }
                }
            ),
        }

    agent = get_agent(agent_id)
    if not agent:
        return {
            "statusCode": 404,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {
                    "error": {
                        "code": "AGENT_NOT_FOUND",
                        "message": f"Agent '{agent_id}' was not found.",
                    }
                }
            ),
        }

    payload = {
        "agent": {
            "id": agent["id"],
            "npn": agent["npn"],
            "firstName": agent["firstName"],
            "lastName": agent["lastName"],
            "currentImo": agent["currentImo"],
        },
        "carriers": agent["carriers"],
        "bookOfBusiness": agent["bookOfBusiness"],
        "requiredSubmissionPayload": {
            "agentId": agent["id"],
            "targetImo": {
                "name": "",
                "fein": "",
            },
            "selectedCarrierIds": [],
            "selectedBookIds": [],
            "effectiveDate": "YYYY-MM-DD",
            "requirementAnswers": {
                "releaseLetterProvided": False,
                "signedTransferPacketProvided": False,
                "daysInCurrentHierarchy": 0,
            },
            "attestation": {
                "agentApproved": False,
                "acknowledgedAt": "YYYY-MM-DDTHH:MM:SSZ",
            },
        },
    }

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(payload),
    }
