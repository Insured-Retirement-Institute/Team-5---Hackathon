# ATS Webhook Receiver (Python)

Minimal FastAPI receiver for `transfer.status.updated` events from the centralized hub.

## Prerequisites

- Python 3.12+

## Install dependencies

```bash
python3 -m pip install -r src/webhooks/receiver/requirements.txt
```

## Configure

Create a local config file from the template:

```bash
cp src/webhooks/receiver/.env.example src/webhooks/receiver/.env
```

The receiver auto-loads `src/webhooks/receiver/.env` on startup.

Set shared webhook secret:

```bash
ATS_WEBHOOK_SECRET='your-strong-shared-secret'
```

Optional DynamoDB persistence:

```bash
DYNAMODB_TABLE_NAME='book-of-business-transfers'
DYNAMODB_PK_NAME='transferId'
AWS_REGION='us-east-1'
```

Optional for local DynamoDB:

```bash
DYNAMODB_ENDPOINT_URL='http://localhost:8001'
```

## Run locally

```bash
uvicorn app:app --app-dir src/webhooks/receiver --host 0.0.0.0 --port 8000 --reload
```

Endpoints:

- `GET /health`
- `POST /hooks/ats-status`

## Behavior

- Verifies `X-ATS-Signature` using HMAC SHA-256 over raw request body.
- Accepts signature as hex or `sha256=<hex>`.
- Uses `X-ATS-Event-Id` for idempotency/de-duplication.
- Updates transfer status record in DynamoDB when `DYNAMODB_TABLE_NAME` is configured.
- Returns `200` for processed and duplicate-ignored events.
- Returns `401` for invalid signature.

## CSV loaders (DynamoDB)

Use the loader script to seed DynamoDB from CSV files:

```bash
chmod +x src/webhooks/receiver/load-status-dynamodb.sh
```

Defaults by file name:

- `results.csv` -> table `Status`
- `book-of-business.csv` -> table `BookOfBusiness`

Examples:

```bash
# Load status seed data (defaults to Status)
src/webhooks/receiver/load-status-dynamodb.sh src/webhooks/receiver/results.csv

# Load fake book of business data (defaults to BookOfBusiness)
src/webhooks/receiver/load-status-dynamodb.sh src/webhooks/receiver/book-of-business.csv

# Explicit table override
src/webhooks/receiver/load-status-dynamodb.sh src/webhooks/receiver/book-of-business.csv MyCustomTable

# Explicit AWS profile override
src/webhooks/receiver/load-status-dynamodb.sh src/webhooks/receiver/results.csv Status iri
```

The loader defaults to AWS profile `iri`. You can override with `AWS_PROFILE` or the 3rd script argument.

For local DynamoDB, set:

```bash
export DYNAMODB_ENDPOINT_URL='http://localhost:8001'
```

## Lambda handler

Lambda entrypoint is in `src/webhooks/receiver/handler.py` as:

- `handler.lambda_handler`

## Local test with curl

```bash
SIG=$(cat src/webhooks/receiver/examples/payload.json | openssl dgst -sha256 -hmac "$ATS_WEBHOOK_SECRET" -hex | sed 's/^.* //')

curl -i -X POST http://localhost:8000/hooks/ats-status \
  -H "Content-Type: application/json" \
  -H "X-ATS-Signature: sha256=$SIG" \
  -H "X-ATS-Event-Id: evt_local_001" \
  --data @src/webhooks/receiver/examples/payload.json
```
