import json

try:
    from .data import get_agent_by_npn
except ImportError:
    from data import get_agent_by_npn


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
}


def lambda_handler(event, context):
    path_parameters = event.get("pathParameters") or {}
    agent_npn = path_parameters.get("npn") or path_parameters.get("id")
    if not agent_npn:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {
                    "error": {
                        "code": "MISSING_AGENT_NPN",
                        "message": "Path parameter 'npn' (or legacy 'id') is required.",
                    }
                }
            ),
        }

    agent = get_agent_by_npn(agent_npn)
    if not agent:
        return {
            "statusCode": 404,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {
                    "error": {
                        "code": "AGENT_NOT_FOUND",
                        "message": f"Agent with NPN '{agent_npn}' was not found.",
                    }
                }
            ),
        }

    payload = {
        "agent": {
            "npn": agent["npn"],
            "firstName": agent["firstName"],
            "lastName": agent["lastName"],
            "currentImo": agent["currentImo"],
        },
        "carriers": agent["carriers"],
        "bookOfBusiness": agent["bookOfBusiness"],
        "requiredSubmissionPayload": {
            "agentNpn": agent["npn"],
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
