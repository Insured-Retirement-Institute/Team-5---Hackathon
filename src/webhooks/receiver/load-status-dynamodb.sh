#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CSV_PATH="${1:-$SCRIPT_DIR/results.csv}"
AWS_REGION_VALUE="${AWS_REGION:-us-east-1}"
DDB_ENDPOINT_URL="${DYNAMODB_ENDPOINT_URL:-}"
AWS_PROFILE_VALUE="${3:-${AWS_PROFILE:-iri}}"

default_table_for_csv() {
  local csv_file="$1"
  local name
  name="$(basename "$csv_file")"

  case "$name" in
    book-of-business.csv) echo "BookOfBusiness" ;;
    results.csv) echo "Status" ;;
    *) echo "Status" ;;
  esac
}

TABLE_NAME="${2:-${TABLE_NAME:-$(default_table_for_csv "$CSV_PATH")}}"

if ! command -v aws >/dev/null 2>&1; then
  echo "Error: aws CLI is required." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required." >&2
  exit 1
fi

if [[ ! -f "$CSV_PATH" ]]; then
  echo "Error: CSV file not found: $CSV_PATH" >&2
  exit 1
fi

if [[ -z "$TABLE_NAME" ]]; then
  echo "Error: TABLE_NAME could not be resolved. Provide it as arg2 or env var TABLE_NAME." >&2
  exit 1
fi

if [[ -z "$AWS_PROFILE_VALUE" ]]; then
  echo "Error: AWS profile could not be resolved. Provide it as arg3 or env var AWS_PROFILE." >&2
  exit 1
fi

echo "Loading CSV into DynamoDB table '$TABLE_NAME' from '$CSV_PATH'..."
echo "Using AWS profile '$AWS_PROFILE_VALUE' in region '$AWS_REGION_VALUE'..."

if [[ -n "$DDB_ENDPOINT_URL" ]]; then
  ENDPOINT_ARGS=(--endpoint-url "$DDB_ENDPOINT_URL")
else
  ENDPOINT_ARGS=()
fi

python3 - "$CSV_PATH" <<'PY' | while IFS= read -r item_json; do
import csv
import json
import sys

csv_path = sys.argv[1]
with open(csv_path, newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        item = {}
        for key, value in row.items():
            if key is None:
                continue
            cell = "" if value is None else str(value).strip()
            if cell == "":
                continue
            item[key] = {"S": cell}
        if item:
            print(json.dumps(item, separators=(",", ":")))
PY
  aws dynamodb put-item \
    --table-name "$TABLE_NAME" \
    --item "$item_json" \
    --profile "$AWS_PROFILE_VALUE" \
    --region "$AWS_REGION_VALUE" \
    "${ENDPOINT_ARGS[@]}" >/dev/null
  echo "Inserted item: $item_json"
done

echo "Done."
