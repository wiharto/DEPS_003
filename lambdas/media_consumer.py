
import os
import json
import boto3 as boto
from datetime import datetime


"""
Entry point to execute the lambda function.

Action:
- Receives messages from media queue.
- Parse messages based on media_key.
- Put data into s3 bucket partitioned by year, month and day.
"""
def handler(event, context):
    # Access s3
    s3 = boto.client('s3')
    bucket_name = os.environ["S3_BUCKET_NAME"]

    # Get year, month, day for bucket partitions
    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year

    # Parse media data based on media_key
    for record in event["Records"]:
        data = json.loads(record["body"])
        for each_data in data:
            filename = f"{each_data['media_key']}.json"
            json_str = json.dumps(each_data, indent=2, default=str)
            try:
                s3.put_object(
                    Bucket = bucket_name,
                    Key = f"{year}/{month}/{day}/{filename}",
                    Body = json_str
                )
                print(f"{filename} is in bucket")
            except Exception as e:
                return e
            
    return f'SUCCESS: all media files are inserted into {os.environ["S3_BUCKET_NAME"]} bucket'

