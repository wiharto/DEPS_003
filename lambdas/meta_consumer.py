

import os
import json
import boto3 as boto
from datetime import datetime, timezone


"""
Entry point to execute the lambda function.

Action: 
- receives messages from meta queue.
- parse messages.
- put each meta data into dynamoDB table.
"""
def handler(event, context):
    # Get datetime
    utc_now = datetime.now(timezone.utc).strftime("%m/%d/%Y %H:%M:%S")
    # Access dynamoDB table
    dynamodb = boto.resource("dynamodb")
    table_name = os.environ["DYNAMODB_META_TABLE_NAME"]
    table = dynamodb.Table(table_name)

    # Parse messages from tweet queue and put to table
    records = event["Records"]
    for record in records:
        data = record["body"]
        data = json.loads(data)
        data['created_at'] = utc_now
        try:
            table.put_item(Item = data)
            print(f"{data} is inserted into table")
        except Exception as e:
            return e
        
    return f'SUCCESS: all items are inserted into {os.environ["DYNAMODB_META_TABLE_NAME"]}'
        
