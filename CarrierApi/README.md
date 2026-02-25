# AtsAgentApi - Python Lambda Version

## Overview
Python Lambda implementation of the AtsAgentApi with API Gateway integration for agent-initiated transfers between IMOs and carriers.

## Architecture
- **AWS Lambda**: Serverless function handling all API logic
- **API Gateway**: REST API frontend with CORS support
- **SAM**: Infrastructure as Code deployment

## Project Structure
```
Carrier/
├── lambda_function.py      # Main Lambda handler with all models and logic
├── template.yaml          # SAM CloudFormation template
├── requirements.txt       # Python dependencies (empty - uses stdlib only)
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## API Endpoints
- `GET /ats/transfers` - List transfers
- `POST /ats/transfers` - Create transfer
- `GET /ats/transfers/{id}` - Get transfer by ID
- `PATCH /ats/transfers/{id}` - Update transfer

## Deployment

### Prerequisites
- AWS CLI configured
- AWS SAM CLI installed
- Python 3.9+

### Deploy
```bash
# Make deploy script executable (Linux/Mac)
chmod +x deploy.sh

# Deploy
./deploy.sh
```

Or manually:
```bash
sam build
sam deploy --guided
```

### Local Testing
```bash
sam local start-api
```

## Example Usage
```bash
# List transfers
curl https://your-api-id.execute-api.region.amazonaws.com/prod/ats/transfers

# Create transfer
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/ats/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "agent": {"npn": "12345", "first_name": "John", "last_name": "Doe"},
    "releasing_imo": {"fein": "12-3456789", "name": "Old IMO"},
    "receiving_imo": {"fein": "98-7654321", "name": "New IMO"},
    "effective_date": "2026-03-01",
    "consent": {"agent_attestation": true}
  }'
```