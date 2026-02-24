import json


def lambda_handler(event, context):
    # Path parameter
    transfer_id = (event.get("pathParameters") or {}).get("id")  # Required: transfer id

    # TODO: implement get transfer logic

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({}),
    }
