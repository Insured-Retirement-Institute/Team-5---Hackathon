#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_FILE="${1:-$SCRIPT_DIR/payload.json}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:5000/hooks/ats-status}"
ATS_WEBHOOK_SECRET="${ATS_WEBHOOK_SECRET:-local-dev-shared-secret}"

if [[ ! -f "$PAYLOAD_FILE" ]]; then
  echo "Payload file not found: $PAYLOAD_FILE"
  exit 1
fi

EVENT_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("eventId","evt_local_missing"))' "$PAYLOAD_FILE")"
SIGNATURE="$(openssl dgst -sha256 -hmac "$ATS_WEBHOOK_SECRET" -hex "$PAYLOAD_FILE" | awk '{print $NF}')"

echo "Sending webhook to: $WEBHOOK_URL"
echo "Using Event ID: $EVENT_ID"

echo
curl -i -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-ATS-Signature: sha256=$SIGNATURE" \
  -H "X-ATS-Event-Id: $EVENT_ID" \
  --data @"$PAYLOAD_FILE"
echo
