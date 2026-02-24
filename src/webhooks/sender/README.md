# ATS Webhook Sender Example (C#)

Simple console app that signs a webhook payload and sends it to the webhook receiver.

## Run

```bash
ATS_WEBHOOK_SECRET='local-dev-shared-secret' \
WEBHOOK_URL='http://localhost:5000/hooks/ats-status' \
dotnet run --project src/webhooks/sender/AtsWebhookSender.Example.csproj
```

Optional payload override:

```bash
dotnet run --project src/webhooks/sender/AtsWebhookSender.Example.csproj -- src/webhooks/receiver/examples/payload.json
```

## Inputs

- `ATS_WEBHOOK_SECRET`: shared HMAC secret used for `X-ATS-Signature`
- `WEBHOOK_URL`: target webhook URL
- `SENDER_DELAY_MS` (optional): delay before sending request (useful when starting receiver and sender together)
- `SENDER_AUTO_SEND` (optional): set `true`/`1` to skip Enter confirmation before each send
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
