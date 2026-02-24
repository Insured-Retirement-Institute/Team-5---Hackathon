#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD_FILE="${1:-$SCRIPT_DIR/payload.json}"
HTTP_FILE="${2:-$SCRIPT_DIR/webhook.http}"
ATS_WEBHOOK_SECRET="${ATS_WEBHOOK_SECRET:-local-dev-shared-secret}"

if [[ ! -f "$PAYLOAD_FILE" ]]; then
  echo "Payload file not found: $PAYLOAD_FILE"
  exit 1
fi

if [[ ! -f "$HTTP_FILE" ]]; then
  echo "HTTP file not found: $HTTP_FILE"
  exit 1
fi

EVENT_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("eventId","evt_local_missing"))' "$PAYLOAD_FILE")"
SIGNATURE="$(openssl dgst -sha256 -hmac "$ATS_WEBHOOK_SECRET" -hex "$PAYLOAD_FILE" | awk '{print $NF}')"

python3 - "$HTTP_FILE" "$EVENT_ID" "$SIGNATURE" <<'PY'
import pathlib
import re
import sys

http_path = pathlib.Path(sys.argv[1])
event_id = sys.argv[2]
signature = sys.argv[3]
text = http_path.read_text(encoding="utf-8")
text = re.sub(r"^@eventId\s*=\s*.*$", f"@eventId = {event_id}", text, flags=re.MULTILINE)
text = re.sub(r"^@signature\s*=\s*.*$", f"@signature = {signature}", text, flags=re.MULTILINE)
http_path.write_text(text, encoding="utf-8")
PY

echo "Updated $HTTP_FILE"
echo "  eventId   = $EVENT_ID"
echo "  signature = $SIGNATURE"
