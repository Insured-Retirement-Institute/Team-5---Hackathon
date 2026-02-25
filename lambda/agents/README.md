# ATS Agents Local Testing

Run the new agents endpoints locally without API Gateway.

## 1) Install dependencies

```bash
python3 -m pip install -r lambda/requirements.txt
```

## 2) Start local API

```bash
python3 lambda/agents/local_api.py
```

Local base URL:

- `http://localhost:8010`

## 3) Test endpoints

### List agents

```bash
curl -s http://localhost:8010/ats/agents | jq
```

### Get agent transfer details

```bash
curl -s http://localhost:8010/ats/agents/agt_1001/validate | jq
```

### Validate transfer payload

```bash
curl -s -X POST http://localhost:8010/ats/agents/agt_1001/validate \
  -H 'Content-Type: application/json' \
  --data @lambda/agents/examples/transfer-agt-1001-valid.json | jq

curl -s -X POST http://localhost:8010/ats/agents/agt_1002/validate \
  -H 'Content-Type: application/json' \
  --data @lambda/agents/examples/transfer-agt-1002-valid.json | jq

curl -s -X POST http://localhost:8010/ats/agents/agt_1001/validate \
  -H 'Content-Type: application/json' \
  --data @lambda/agents/examples/transfer-agt-1001-invalid.json | jq
```

## Postman collection

Import this collection for ready-to-run local requests:

- `lambda/agents/examples/ats-agents-local.postman_collection.json`

The collection uses `{{baseUrl}}` with default value `http://localhost:8010`.
