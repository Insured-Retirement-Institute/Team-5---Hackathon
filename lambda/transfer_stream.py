def lambda_handler(event, context):
    for record in event["Records"]:
        event_name = record["eventName"]  # INSERT | MODIFY | REMOVE
        new_image = record["dynamodb"].get("NewImage", {})  # item after the change
        # old_image  = record["dynamodb"].get("OldImage", {}) # item before the change (MODIFY/REMOVE only)

        # DynamoDB stream values are typed: {"S": "value"}, {"N": "123"}, {"BOOL": True}
        transfer_id = new_image.get("id", {}).get("S")
        state = new_image.get("state", {}).get("S")
