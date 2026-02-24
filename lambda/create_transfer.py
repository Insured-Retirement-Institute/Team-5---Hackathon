import json
import os

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TRANSFERS_TABLE"])


def lambda_handler(event, context):
    # Headers
    headers = event.get("headers") or {}
    idempotency_key = headers.get(
        "Idempotency-Key"
    )  # Optional: safely retry POST without creating duplicates

    # Request body
    body = json.loads(event.get("body") or "{}")

    # Agent (required)
    agent = body.get("agent", {})
    agent_npn = agent.get("npn")  # Required: National Producer Number
    agent_first_name = agent.get("firstName")  # Optional
    agent_last_name = agent.get("lastName")  # Optional

    # Releasing IMO (required)
    releasing_imo = body.get("releasingImo", {})
    releasing_imo_fein = releasing_imo.get("fein")  # Required: Business FEIN
    releasing_imo_name = releasing_imo.get("name")  # Required

    # Receiving IMO (required)
    receiving_imo = body.get("receivingImo", {})
    receiving_imo_fein = receiving_imo.get("fein")  # Required: Business FEIN
    receiving_imo_name = receiving_imo.get("name")  # Required

    # Transfer details
    effective_date = body.get(
        "effectiveDate"
    )  # Required: target date for hierarchy/commission realignment (YYYY-MM-DD)

    # Consent (required)
    consent = body.get("consent", {})
    agent_attestation = consent.get(
        "agentAttestation"
    )  # Required: True if agent has authorized this transfer
    e_signature_ref = consent.get(
        "eSignatureRef"
    )  # Optional: reference to e-signature artifact

    # Optional notes
    notes = body.get(
        "notes"
    )  # Optional: free text for carrier processing (max 2000 chars)

    key = f"{receiving_imo_fein}|{releasing_imo_fein}|{agent_npn}"

    item = {
        "id": key,
        "state": "SUBMITTED",
        "agentNpn": agent_npn,
        "agentFirstName": agent_first_name,
        "agentLastName": agent_last_name,
        "releasingImoFein": releasing_imo_fein,
        "releasingImoName": releasing_imo_name,
        "receivingImoFein": receiving_imo_fein,
        "receivingImoName": receiving_imo_name,
        "effectiveDate": effective_date,
        "agentAttestation": agent_attestation,
        "eSignatureRef": e_signature_ref,
        "notes": notes,
        "idempotencyKey": idempotency_key,
    }

    # Remove None values so DynamoDB doesn't reject them
    item = {k: v for k, v in item.items() if v is not None}

    table.put_item(Item=item)

    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Location": f"/ats/transfers/{key}",
        },
        "body": json.dumps({"id": key, "state": "SUBMITTED"}),
    }
