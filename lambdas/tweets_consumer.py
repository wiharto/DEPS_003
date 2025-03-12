
import os
import json
import boto3 as boto


"""
Entry point to execute the lambda function.

Action: 
- receives messages from tweet queue.
- parse messages into each tweet.
- put each tweet into dynamoDB table.
"""
def handler(event, context):
    # Access dynamoDB table
    dynamodb = boto.resource("dynamodb")
    table_name = os.environ["DYNAMODB_TWEET_TABLE_NAME"]
    table = dynamodb.Table(table_name)

    # Parse messages from tweet queue and put to table
    records = event["Records"]
    for record in records:
        print(f"RECORD: {record}")
        data = json.loads(record["body"])
        for each in data:
            print(f"EACH DATA: {each}")
            try:
                table.put_item(Item = each)
            except Exception as e:
                return e
        
    return f'SUCCESS: all items are inserted into {os.environ["DYNAMODB_TWEET_TABLE_NAME"]}'
        
