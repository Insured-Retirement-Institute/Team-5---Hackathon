# Define repoistory name

Define description. Test

## Get started

We are currently in the process of standing up [SwaggerHub](https://wwww.swaggerhub.com) to host OpenAPI definitions. More to come.

## Python setup (3.12)

Create and activate a Python 3.12 virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

Install project dependencies:

```bash
pip install -r lambda/requirements.txt -r CarrierApi/requirements.txt -r team5_ai/webapp/requirements.txt
```

## SAM deploy quickstart

This repo includes `samconfig.toml` configured for profile `iri`.

Build and deploy the full ATS stack:

```bash
sam build
sam deploy
```

Deploy only updated agents Lambda code (no infrastructure changes):

```bash
sam sync --code \
	--resource-id ListAgentsFunction \
	--resource-id GetAgentValidateFunction \
	--resource-id PostAgentValidateFunction
```

Deploy agents-only template to existing API Gateway:

```bash
./scripts/deploy-agents.sh
```

Note: both deployment templates (`template.yaml` and `template-agents.yaml`) use NPN-based agent routes: `/ats/agents/{npn}/validate`.

Optional overrides:

```bash
AWS_PROFILE=iri AWS_REGION=us-east-1 SOURCE_STACK=ats-api AGENTS_STACK=ats-agents STAGE_NAME=prod ./scripts/deploy-agents.sh

# If SOURCE_STACK has no AtsApiUrl output, provide API directly:
EXISTING_REST_API_ID=21yem0s5jl AWS_PROFILE=iri AWS_REGION=us-east-1 ./scripts/deploy-agents.sh

# Or resolve by API name (default is hackathon):
API_NAME=hackathon AWS_PROFILE=iri AWS_REGION=us-east-1 ./scripts/deploy-agents.sh
```

## API Gateway route mapping (Lambda)

Use these route-to-handler mappings for ATS endpoints:

Transfer endpoints:

- `GET /ats/transfers` -> `lambda/list_transfers.lambda_handler`
- `POST /ats/transfers` -> `lambda/create_transfer.lambda_handler`
- `GET /ats/transfers/{id}` -> `lambda/get_transfer.lambda_handler`
- `PATCH /ats/transfers/{id}` -> `lambda/patch_transfer.lambda_handler`

Status endpoints:

- `POST /ats/status` -> `lambda/set_status.lambda_handler`
- `GET /ats/status/{fein}` -> `lambda/get_statuses.lambda_handler`

Agent transfer endpoints:

- `GET /ats/agents` -> `lambda/agents/list_agents.lambda_handler`
- `GET /ats/agents/{npn}/validate` -> `lambda/agents/get_agent_transfer.lambda_handler`
- `POST /ats/agents/{npn}/validate` -> `lambda/agents/post_agent_transfer.lambda_handler`

Related files:

- `lambda/agents/data.py` (shared sample data and lookup helpers)
- `openapi_agent_api.yaml` (API contract for all ATS endpoints)

Please refer to the [style guide](https://github.com/Insured-Retirement-Institute/Style-Guide) for technical governance of standards, data dictionary, and the code of conduct.

## Business Case

Define your business case for the specification.

## User Stories, personna - supporting documents for the business case

- Load your user stories, personna - supporting documents for the business case.

## Business Owners

- Carrier Business Owner: contact
- Distributor Business Owner: contact
- Solution Provider Business Owner: contact

## How to engage, contribute, and give feedback

- These working groups are occuring on ....
- Please contact the business owners or IRI (hpikus@irionline.org) to get added to the working group discussions.

## Change subsmissions and reporting issues and bugs

Security issues and bugs should be reported directly to Katherine Dease kdease@irionline.org. Issues and bugs can be reported directly within the issues tab of a repository. Change requests should follow the standards governance workflow outlined on the [main page](https://github.com/Insured-Retirement-Institute).

## Code of conduct

See [style guide](https://github.com/Insured-Retirement-Institute/Style-Guide)

TODO:
Confirm target stack/API:
aws cloudformation describe-stacks --stack-name <his-stack> --query "Stacks[0].Parameters" --output table
Confirm agent resources exist in that API:
aws apigateway get-resources --rest-api-id <api-id> --limit 500 --query "items[?starts_with(path, '/ats/agents')].[path,id]" --output table
If he only needs code updates, skip infra changes:
sam sync --code --resource-id ListAgentsFunction --resource-id GetAgentValidateFunction --resource-id PostAgentValidateFunction
