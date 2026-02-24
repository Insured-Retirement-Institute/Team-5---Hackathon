# ATS Webhook Receiver (C#)

Minimal ASP.NET Core receiver for `transfer.status.updated` events from the centralized hub.

## Prerequisites

- .NET 10 SDK

## Configure

Use either:

- Environment variable `ATS_WEBHOOK_SECRET` (recommended), or
- `AtsWebhook:Secret` in `appsettings.json`.

Example:

```bash
export ATS_WEBHOOK_SECRET='your-strong-shared-secret'
```

## Run

```bash
dotnet run --project src/webhooks/receiver/AtsWebhookReceiver.csproj
```

The webhook endpoint is:

- `POST /hooks/ats-status`

## Debug locally (step through code)

This repo includes VS Code debug config in `.vscode/launch.json`.

1. Open the workspace in VS Code.
2. Go to Run and Debug.
3. Select **Debug ATS Webhook Receiver**.
4. Set breakpoints in `Program.cs` (for example inside the `/hooks/ats-status` handler).
5. Start debugging with `F5`.

The launch configuration sets:

- `ATS_WEBHOOK_SECRET=local-dev-shared-secret`
- `ASPNETCORE_ENVIRONMENT=Development`

## Execute webhook example

Use the included example payload and sender script:

```bash
chmod +x src/webhooks/receiver/examples/send-webhook.sh
./src/webhooks/receiver/examples/send-webhook.sh
```

Optional overrides:

```bash
ATS_WEBHOOK_SECRET='local-dev-shared-secret' \
WEBHOOK_URL='http://localhost:5000/hooks/ats-status' \
./src/webhooks/receiver/examples/send-webhook.sh src/webhooks/receiver/examples/payload.json
```

Files:

- Payload: `src/webhooks/receiver/examples/payload.json`
- Script: `src/webhooks/receiver/examples/send-webhook.sh`
- REST Client request: `src/webhooks/receiver/examples/webhook.http`
- REST Client updater: `src/webhooks/receiver/examples/update-webhook-http.sh`

Update `webhook.http` automatically before sending from VS Code REST Client:

```bash
chmod +x src/webhooks/receiver/examples/update-webhook-http.sh
./src/webhooks/receiver/examples/update-webhook-http.sh
```

Then open `src/webhooks/receiver/examples/webhook.http` and click **Send Request** on the webhook request.

## Behavior

- Verifies `X-ATS-Signature` using HMAC SHA-256 over the raw request body.
- Accepts signature as either hex or `sha256=<hex>` format.
- Uses `X-ATS-Event-Id` for idempotency and deduplication.
- Logs processed events with transfer ID and state transition.
- Returns `200` for processed events and for duplicates (`duplicate_ignored`).
- Returns `401` for invalid signatures.

## Test with curl

Create a payload file (for example `payload.json`), then compute signature and send:

```bash
SIG=$(cat payload.json | openssl dgst -sha256 -hmac "$ATS_WEBHOOK_SECRET" -hex | sed 's/^.* //')

curl -i -X POST http://localhost:5000/hooks/ats-status \
  -H "Content-Type: application/json" \
  -H "X-ATS-Signature: sha256=$SIG" \
  -H "X-ATS-Event-Id: evt_01J91S3M7N8AQ5KQ9QETQJ8B2R" \
  --data @payload.json
```
