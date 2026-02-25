import csv
import uuid

import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("Contracts")

with open("contracts.csv", newline="") as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    with table.batch_writer() as batch:
        for row in reader:
            batch.put_item(
                Item={
                    "id": str(uuid.uuid4()),
                    "contractNumber": row["contractNumber"].strip(),
                    "carrierId": row["carrierId"].strip(),
                    "fein": row["fein"].strip(),
                    "npn": row["npn"].strip(),
                    "contractType": row["contractType"].strip(),
                    "contractValue": row["contractValue"].strip(),
                    "issueDate": row["issueDate"].strip(),
                }
            )

print("Done — 100 contracts uploaded.")
