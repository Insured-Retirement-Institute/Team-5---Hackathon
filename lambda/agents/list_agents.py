import json

try:
    from .data import list_agents
except ImportError:
    from data import list_agents


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Idempotency-Key",
}


def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    receiving_imo_fein = query_params.get("receivingImoFein")

    agents = list_agents(receiving_imo_fein=receiving_imo_fein)

    response_payload = [
        {
            "id": agent["id"],
            "npn": agent["npn"],
            "firstName": agent["firstName"],
            "lastName": agent["lastName"],
            "currentImo": agent["currentImo"],
            "carriers": [
                {
                    "carrierId": carrier["carrierId"],
                    "carrierName": carrier["carrierName"],
                    "licensed": carrier["licensed"],
                }
                for carrier in agent["carriers"]
            ],
            "bookOfBusiness": agent["bookOfBusiness"],
        }
        for agent in agents
    ]

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(response_payload),
    }
