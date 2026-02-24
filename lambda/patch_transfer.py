import json


def lambda_handler(event, context):
    # Path parameter
    transfer_id = (event.get("pathParameters") or {}).get("id")  # Required: transfer id

    # Request body
    body = json.loads(event.get("body") or "{}")

    action = body.get("action")  # Required: CANCEL | ADD_NOTE
    note = body.get("note")  # Used when action=ADD_NOTE
    reason = body.get("reason")  # Optional: human-readable reason (e.g., for CANCEL)

    # TODO: implement patch transfer logic

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({}),
    }
