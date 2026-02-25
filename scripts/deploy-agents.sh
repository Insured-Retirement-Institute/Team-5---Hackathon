#!/usr/bin/env bash
set -euo pipefail

PROFILE="${AWS_PROFILE:-iri}"
REGION="${AWS_REGION:-us-east-1}"
SOURCE_STACK="${SOURCE_STACK:-ats-api}"
AGENTS_STACK="${AGENTS_STACK:-ats-agents}"
STAGE_NAME="${STAGE_NAME:-prod}"
TEMPLATE_FILE="${TEMPLATE_FILE:-template-agents.yaml}"
EXISTING_REST_API_ID="${EXISTING_REST_API_ID:-}"
API_NAME="${API_NAME:-hackathon}"

if ! command -v aws >/dev/null 2>&1; then
  echo "Error: aws CLI is required." >&2
  exit 1
fi

if ! command -v sam >/dev/null 2>&1; then
  echo "Error: sam CLI is required." >&2
  exit 1
fi

echo "Using profile=$PROFILE region=$REGION source_stack=$SOURCE_STACK agents_stack=$AGENTS_STACK stage=$STAGE_NAME"

REST_API_ID="$EXISTING_REST_API_ID"

if [[ -z "$REST_API_ID" ]]; then
  API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$SOURCE_STACK" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='AtsApiUrl'].OutputValue" \
    --output text 2>/dev/null || true)

  if [[ -n "$API_URL" && "$API_URL" != "None" ]]; then
    REST_API_ID=$(echo "$API_URL" | sed -E 's#https://([^.]+)\..*#\1#')
  fi
fi

if [[ -z "$REST_API_ID" ]]; then
  REST_API_ID=$(aws apigateway get-rest-apis \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "items[?name=='${API_NAME}'].id | [0]" \
    --output text)

  if [[ -z "$REST_API_ID" || "$REST_API_ID" == "None" ]]; then
    echo "Error: Could not resolve REST API ID. Set EXISTING_REST_API_ID or ensure SOURCE_STACK output/APl_NAME lookup works." >&2
    exit 1
  fi
fi

ATS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "items[?path=='/ats'].id | [0]" \
  --output text)

if [[ -z "$ATS_RESOURCE_ID" || "$ATS_RESOURCE_ID" == "None" ]]; then
  ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$REST_API_ID" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "items[?path=='/'].id | [0]" \
    --output text)

  if [[ -z "$ROOT_RESOURCE_ID" || "$ROOT_RESOURCE_ID" == "None" ]]; then
    echo "Error: Could not resolve root resource '/' for API '$REST_API_ID'." >&2
    exit 1
  fi

  ATS_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$REST_API_ID" \
    --parent-id "$ROOT_RESOURCE_ID" \
    --path-part ats \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "id" \
    --output text)

  echo "Created missing /ats resource with id=$ATS_RESOURCE_ID"
fi

echo "Resolved REST_API_ID=$REST_API_ID"
echo "Resolved ATS_RESOURCE_ID=$ATS_RESOURCE_ID"

sam build --template-file "$TEMPLATE_FILE"

sam deploy \
  --template-file "$TEMPLATE_FILE" \
  --stack-name "$AGENTS_STACK" \
  --capabilities CAPABILITY_IAM \
  --profile "$PROFILE" \
  --region "$REGION" \
  --parameter-overrides ExistingRestApiId="$REST_API_ID" ExistingAtsResourceId="$ATS_RESOURCE_ID" StageName="$STAGE_NAME"

echo "Agents deployment completed."
