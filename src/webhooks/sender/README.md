# ATS Webhook Sender Example (Python)

Simple Python script that signs webhook payloads and sends them to the webhook receiver.

## Prerequisites

- Python 3.12+

## Install dependencies

```bash
python3 -m pip install -r src/webhooks/sender/requirements.txt
```

## Run

```bash
ATS_WEBHOOK_SECRET='local-dev-shared-secret' \
WEBHOOK_URL='http://localhost:8000/hooks/ats-status' \
python3 src/webhooks/sender/sender.py
```

Optional payload override:

```bash
python3 src/webhooks/sender/sender.py src/webhooks/receiver/examples/payload.json
```

## Inputs

- `ATS_WEBHOOK_SECRET`: shared HMAC secret used for `X-ATS-Signature`
- `WEBHOOK_URL`: target webhook URL
- `SENDER_DELAY_MS` (optional): delay before sending request (useful when starting receiver and sender together)
- `SENDER_AUTO_SEND` (optional): set `true`/`1` to skip Enter confirmation before each send
- `AWS_SIGN_REQUEST` (optional): set `true`/`1` to SigV4-sign request for IAM-protected endpoints
- `AWS_REGION` (optional): region used for SigV4 signing (auto-detected from AWS URL when possible)
- `AWS_SIGV4_SERVICE` (optional): SigV4 service name, default `lambda` (`execute-api` for API Gateway)
- First CLI argument (optional): payload JSON file path

## Behavior

- Loads JSON payload from file
- Requires status input each time (updates `data.state`)
- Accepts only: `SUBMITTED`, `VALIDATION`, `PROCESSING`, `COMPLETED`, `REJECTED`, `WITHDRAWN`
- Generates a new `eventId` and `occurredAt` for each send
- Sets `data.previousState` to the previously sent status
- Computes `sha256=<hex>` signature over raw payload bytes
- Waits for Enter before sending (unless `SENDER_AUTO_SEND=true`)
- Repeats status prompts continuously until you stop the process
- Sends `POST` with headers:
  - `X-ATS-Event-Id`
  - `X-ATS-Signature`

## Troubleshooting 403 Forbidden

`403` usually means the request is blocked before payload validation:

- Verify `WEBHOOK_URL` path is correct.
- For IAM-protected Lambda/API Gateway endpoints, set `AWS_SIGN_REQUEST=true` and `AWS_REGION`.
- For Lambda Function URLs with auth type `NONE`, keep `AWS_SIGN_REQUEST` disabled.
- On localhost targets, sender runs a startup probe to `GET /health` and warns if the response looks like macOS AirTunes/ControlCenter.
