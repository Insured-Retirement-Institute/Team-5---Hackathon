import json


def lambda_handler(event, context):
    # Query string parameters
    query_params = event.get("queryStringParameters") or {}

    npn = query_params.get("npn")  # Optional: agent NPN to filter results
    state = query_params.get(
        "state"
    )  # Optional: TransferState filter (SUBMITTED|VALIDATION|PROCESSING|COMPLETED|REJECTED|WITHDRAWN)
    limit = int(query_params.get("limit", 25))  # Default 25, min 1, max 100

    # TODO: implement list transfers logic

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps([]),
    }
