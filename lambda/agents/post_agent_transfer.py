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
        return _bad_request(
            "MISSING_AGENT_NPN",
            "Path parameter 'npn' (or legacy 'id') is required.",
        )

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

    body = json.loads(event.get("body") or "{}")
    errors = validate_payload(body, agent)

    if errors:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {
                    "valid": False,
                    "errors": errors,
                }
            ),
        }

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(
            {
                "valid": True,
                "agentNpn": agent_npn,
                "message": "Payload is valid for transfer submission.",
            }
        ),
    }


def validate_payload(payload, agent):
    errors = []

    if payload.get("agentNpn") != agent["npn"]:
        errors.append("agentNpn must match path parameter npn.")

    target_imo = payload.get("targetImo") or {}
    target_name = target_imo.get("name")
    target_fein = target_imo.get("fein")
    if not target_name or not target_fein:
        errors.append("targetImo.name and targetImo.fein are required.")

    selected_carrier_ids = payload.get("selectedCarrierIds")
    if not isinstance(selected_carrier_ids, list) or not selected_carrier_ids:
        errors.append("selectedCarrierIds must be a non-empty array.")
        selected_carrier_ids = []

    selected_book_ids = payload.get("selectedBookIds")
    if not isinstance(selected_book_ids, list) or not selected_book_ids:
        errors.append("selectedBookIds must be a non-empty array.")
        selected_book_ids = []

    effective_date = payload.get("effectiveDate")
    if not effective_date:
        errors.append("effectiveDate is required.")

    attestation = payload.get("attestation") or {}
    if attestation.get("agentApproved") is not True:
        errors.append("attestation.agentApproved must be true.")

    if not attestation.get("acknowledgedAt"):
        errors.append("attestation.acknowledgedAt is required.")

    licensed_carrier_ids = {
        carrier["carrierId"]
        for carrier in agent.get("carriers", [])
        if carrier.get("licensed") is True
    }

    for carrier_id in selected_carrier_ids:
        if carrier_id not in licensed_carrier_ids:
            errors.append(f"Carrier '{carrier_id}' is not licensed for this agent.")

    valid_book_ids = {book["bookId"] for book in agent.get("bookOfBusiness", [])}
    for book_id in selected_book_ids:
        if book_id not in valid_book_ids:
            errors.append(f"Book '{book_id}' does not belong to this agent.")

    requirement_answers = payload.get("requirementAnswers") or {}
    hierarchy_days = requirement_answers.get("daysInCurrentHierarchy")

    for carrier in agent.get("carriers", []):
        carrier_id = carrier["carrierId"]
        if carrier_id not in selected_carrier_ids:
            continue

        requirements = carrier.get("requirements", {})
        if requirements.get("requiresLetterOfInstruction") and not requirement_answers.get(
            "letterOfInstructionProvided"
        ):
            errors.append(
                f"Carrier '{carrier_id}' requires letterOfInstructionProvided=true."
            )

        if requirements.get("requiresTermsOfInstruction") and not requirement_answers.get(
            "termsOfInstructionProvided"
        ):
            errors.append(
                f"Carrier '{carrier_id}' requires termsOfInstructionProvided=true."
            )

        min_days = requirements.get("minimumDaysInCurrentHierarchy", 0)
        if not isinstance(hierarchy_days, int) or hierarchy_days < min_days:
            errors.append(
                f"Carrier '{carrier_id}' requires daysInCurrentHierarchy >= {min_days}."
            )

    return errors


def _bad_request(code, message):
    return {
        "statusCode": 400,
        "headers": CORS_HEADERS,
        "body": json.dumps(
            {
                "error": {
                    "code": code,
                    "message": message,
                }
            }
        ),
    }
