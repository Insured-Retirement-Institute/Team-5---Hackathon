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
FORCE_CLEAN_BUILD="${FORCE_CLEAN_BUILD:-false}"

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
    echo "Error: Could not resolve REST API ID. Set EXISTING_REST_API_ID or ensure SOURCE_STACK output/API_NAME lookup works." >&2
    exit 1
  fi
fi

ATS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --limit 500 \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "items[?path=='/ats'].id | [0]" \
  --output text)

if [[ -z "$ATS_RESOURCE_ID" || "$ATS_RESOURCE_ID" == "None" ]]; then
  ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id "$REST_API_ID" \
    --limit 500 \
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

AGENTS_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --limit 500 \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "items[?path=='/ats/agents'].id | [0]" \
  --output text)

if [[ "$AGENTS_RESOURCE_ID" == "None" ]]; then
  AGENTS_RESOURCE_ID=""
fi

AGENT_VARIABLE_RESOURCE_ID=""
VALIDATE_RESOURCE_ID=""

if [[ -z "$AGENTS_RESOURCE_ID" ]]; then
  AGENTS_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$REST_API_ID" \
    --parent-id "$ATS_RESOURCE_ID" \
    --path-part agents \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "id" \
    --output text)

  echo "Created missing /ats/agents resource with id=$AGENTS_RESOURCE_ID"
fi

AGENT_VARIABLE_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --limit 500 \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "items[?parentId=='${AGENTS_RESOURCE_ID}' && starts_with(pathPart, '{')].id | [0]" \
  --output text)

if [[ "$AGENT_VARIABLE_RESOURCE_ID" == "None" || -z "$AGENT_VARIABLE_RESOURCE_ID" ]]; then
  AGENT_VARIABLE_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$REST_API_ID" \
    --parent-id "$AGENTS_RESOURCE_ID" \
    --path-part "{id}" \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "id" \
    --output text)

  echo "Created missing /ats/agents/{id} resource with id=$AGENT_VARIABLE_RESOURCE_ID"
fi

VALIDATE_RESOURCE_ID=$(aws apigateway get-resources \
  --rest-api-id "$REST_API_ID" \
  --limit 500 \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query "items[?parentId=='${AGENT_VARIABLE_RESOURCE_ID}' && pathPart=='validate'].id | [0]" \
  --output text)

if [[ "$VALIDATE_RESOURCE_ID" == "None" || -z "$VALIDATE_RESOURCE_ID" ]]; then
  VALIDATE_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id "$REST_API_ID" \
    --parent-id "$AGENT_VARIABLE_RESOURCE_ID" \
    --path-part validate \
    --profile "$PROFILE" \
    --region "$REGION" \
    --query "id" \
    --output text)

  echo "Created missing /ats/agents/{id}/validate resource with id=$VALIDATE_RESOURCE_ID"
fi

echo "Resolved AGENTS_RESOURCE_ID=${AGENTS_RESOURCE_ID:-<create>}"
echo "Resolved AGENT_VARIABLE_RESOURCE_ID=${AGENT_VARIABLE_RESOURCE_ID:-<create>}"
echo "Resolved VALIDATE_RESOURCE_ID=${VALIDATE_RESOURCE_ID:-<create>}"

if [[ "$FORCE_CLEAN_BUILD" == "true" ]]; then
  rm -rf .aws-sam/build .aws-sam/deps
  sam build --template-file "$TEMPLATE_FILE" --no-cached
else
  sam build --template-file "$TEMPLATE_FILE"
fi

PARAM_OVERRIDES=(
  "ExistingRestApiId=$REST_API_ID"
  "ExistingAtsResourceId=$ATS_RESOURCE_ID"
  "ExistingAgentsResourceId=$AGENTS_RESOURCE_ID"
  "ExistingAgentVariableResourceId=$AGENT_VARIABLE_RESOURCE_ID"
  "ExistingValidateResourceId=$VALIDATE_RESOURCE_ID"
  "StageName=$STAGE_NAME"
)

sam deploy \
  --template-file "$TEMPLATE_FILE" \
  --stack-name "$AGENTS_STACK" \
  --capabilities CAPABILITY_IAM \
  --force-upload \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --profile "$PROFILE" \
  --region "$REGION" \
  --parameter-overrides "${PARAM_OVERRIDES[@]}"

LIST_FN_ARN=$(aws lambda get-function \
  --function-name "${AGENTS_STACK}-list-agents" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'Configuration.FunctionArn' \
  --output text)

GET_VALIDATE_FN_ARN=$(aws lambda get-function \
  --function-name "${AGENTS_STACK}-get-agent-validate" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'Configuration.FunctionArn' \
  --output text)

POST_VALIDATE_FN_ARN=$(aws lambda get-function \
  --function-name "${AGENTS_STACK}-post-agent-validate" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --query 'Configuration.FunctionArn' \
  --output text)

upsert_method() {
  local resource_id="$1"
  local http_method="$2"
  local function_arn="$3"

  if ! aws apigateway get-method \
    --rest-api-id "$REST_API_ID" \
    --resource-id "$resource_id" \
    --http-method "$http_method" \
    --profile "$PROFILE" \
    --region "$REGION" >/dev/null 2>&1; then
    aws apigateway put-method \
      --rest-api-id "$REST_API_ID" \
      --resource-id "$resource_id" \
      --http-method "$http_method" \
      --authorization-type NONE \
      --profile "$PROFILE" \
      --region "$REGION" >/dev/null
    echo "Created method $http_method on resource $resource_id"
  fi

  aws apigateway put-integration \
    --rest-api-id "$REST_API_ID" \
    --resource-id "$resource_id" \
    --http-method "$http_method" \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${function_arn}/invocations" \
    --profile "$PROFILE" \
    --region "$REGION" >/dev/null
}

upsert_method "$AGENTS_RESOURCE_ID" "GET" "$LIST_FN_ARN"
upsert_method "$VALIDATE_RESOURCE_ID" "GET" "$GET_VALIDATE_FN_ARN"
upsert_method "$VALIDATE_RESOURCE_ID" "POST" "$POST_VALIDATE_FN_ARN"

aws apigateway create-deployment \
  --rest-api-id "$REST_API_ID" \
  --stage-name "$STAGE_NAME" \
  --profile "$PROFILE" \
  --region "$REGION" >/dev/null

echo "API Gateway stage '${STAGE_NAME}' redeployed with latest method integrations."

echo "Agents deployment completed."
