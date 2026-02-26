import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

TABLES = [
    {"name": "Transfers", "keys": ["id"]},
    {"name": "Contracts", "keys": ["id"]},
    {"name": "Status", "keys": ["receivingFein", "statusKey"]},
]


def clear_table(table_name, key_names):
    table = dynamodb.Table(table_name)
    deleted = 0

    result = table.scan(ProjectionExpression=", ".join(key_names))
    items = result.get("Items", [])

    while True:
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={k: item[k] for k in key_names})
                deleted += 1

        if "LastEvaluatedKey" not in result:
            break
        result = table.scan(
            ProjectionExpression=", ".join(key_names),
            ExclusiveStartKey=result["LastEvaluatedKey"],
        )
        items = result.get("Items", [])

    print(f"{table_name}: deleted {deleted} items")


for t in TABLES:
    clear_table(t["name"], t["keys"])

print("Done.")
