
import requests
import os
import json
import boto3 as boto


# Get bearer token from env var
bearer_token = os.environ["TWITTER_BEARER_TOKEN"]

def create_url():
    user_id = os.environ["TWITTER_USER_ID"]
    return f"https://api.twitter.com/2/users/{user_id}/tweets"


def get_params():
    return {
        "tweet.fields":"author_id,conversation_id,created_at,source,referenced_tweets,text",
        "media.fields":"type,url",
        "expansions":"attachments.media_keys"
    }


def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r


def connect_to_endpoint(url, params):    
    response = requests.request("GET", url, params=params, auth=bearer_oauth)
    
    if response.status_code == 429:
        print(f"Response returned {response.status_code}: Too many requests. Wait 15 minutes.")
        raise Exception(f"Response returned {response.status_code}: Too many requests. Wait 15 minutes.")
    elif response.status_code == 200:
        return response.json()


def parse_response(response):
    # Get tweet_data
    tweet_data = json.dumps(response['data'], indent=2, sort_keys=True)
    # Get media_data
    if 'includes' in response:
        media_data = json.dumps(response['includes']['media'], indent=2, sort_keys=True)
    else:
        media_data = None
    # Get meta_data and add author_id to meta_data
    author_id = response['data'][0]['author_id']
    meta_data = response['meta']
    meta_data['author_id'] = author_id
    meta_data = json.dumps(meta_data, indent=2, sort_keys=True)

    return tweet_data, media_data, meta_data


def send_data_to_queue(data, q_name):
    q_urls = {
        "tweet": "TWEET_QUEUE_URL",
        "media": "MEDIA_QUEUE_URL",
        "meta": "META_QUEUE_URL"}
    
    # Create boto client
    sqs = boto.client('sqs')
    try:
        sqs.send_message(
            QueueUrl = os.environ[q_urls[q_name]],
            MessageBody = data,
        )
        print(f"{q_name.upper()}: sent")
    except Exception as e:
        return e


"""
Entry point to execute the lambda function.

Action: 
- gets user timeline data.
- parse the data into tweet and media data.
- send data to tweet queue and media queue.
"""
def handler(event, context):
    # Processing first page
    # Get twitter user data
    url = create_url()
    params = get_params()
    response = connect_to_endpoint(url, params)
    
    # Parse data into tweet data, media data and meta data
    tweet_data, media_data, meta_data = parse_response(response)

    # Send data to queue
    for i in [(tweet_data, 'tweet'), (media_data, 'media'), (meta_data, 'meta')]:
        if i[0] != None:
            send_data_to_queue(i[0], i[1])

    # Process next pages until twitter api returns 429.
    while response['meta']['next_token']:
        # Add 'pagination_token' param to get to next page
        params = get_params()
        params['pagination_token'] = response['meta']['next_token']
        # Get request
        response = connect_to_endpoint(url, params)
        # Parse data from next page
        tweet_data, media_data, meta_data = parse_response(response)
        # Send data to queue
        for i in [(tweet_data, 'tweet'), (media_data, 'media'), (meta_data, 'meta')]:
            if i[0] != None:
                send_data_to_queue(i[0], i[1])
    
    return {
        'statusCode': 200,
        'body': f'SUCCESS: All data are sent'
    }

