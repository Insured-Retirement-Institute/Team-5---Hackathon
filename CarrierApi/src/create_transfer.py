import json
import time
import urllib.request
import urllib.error
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

@xray_recorder.capture('create_transfer')
def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    
    response_data = {"id": "tr_mocked_id", "state": "SUBMITTED"}
    
    time.sleep(2)
    
    status_payload = {
        "receivingFein": body.get('receivingImo', {}).get('fein', ''),
        "releasingFein": body.get('releasingImo', {}).get('fein', ''),
        "carrierId": "carrier_001",
        "status": "PENDING",
        "npn": body.get('agent', {}).get('npn', '')
    }
    
    with xray_recorder.in_subsegment('notify_ats_status') as subsegment:
        subsegment.put_metadata('payload', status_payload)
        try:
            req = urllib.request.Request(
                'https://21yem0s5jl.execute-api.us-east-1.amazonaws.com/prod/ats/status',
                data=json.dumps(status_payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            urllib.request.urlopen(req)
        except urllib.error.URLError as e:
            subsegment.add_exception(e, fatal=False)
    
    return {
        'statusCode': 200,
        'body': json.dumps(response_data),
        'headers': {'Content-Type': 'application/json'}
    }