The Data Engineering Project Series (DEPS) showcases my expertise in designing and implementing data solutions that address practical challenges. Each project demonstrates proficiency with different technologies and methodologies in the data engineering field, highlighting my ability to build production-ready data pipelines. These independent projects reflect my approach to solving data problems, from initial architecture design to successful implementation. They represent my technical capabilities and problem-solving skills in data engineering.

> [!NOTE]
> The projects in DEPS are demonstration assignments originally created for technical interviews, designed to showcase technical skills and problem-solving capabilities.

# DEPS_003: Twitter(X) API Pipeline Using Python and AWS CDK
## Summary
What this application does:
* Get data (meta, media and tweets) from Twitter(X) API.
* Send data to queues using Amazon SQS.
* Consume and process each data.
* Send each data to either a database (DynamoDB tables) or an S3 bucket.
> [!NOTE]
> At this point Twitter has changed to X and the API may or may not work. However, the concept, architecture and how the tools are used are still valid.

## Tools (As of March 2025)
* Python 3.10
* AWS (CDK, SQS, lambda, DynamoDB, S3, Cloudwatch, Cloudformation)
* Docker

## How To Run This App
> [!NOTE]
> It is recommended to run this app inside of a python virtual environment.

1. `cd` into the `twitter_api` directory.
2. If you have not bootstrapped your AWS CDK, run below commands:
```
$ aws sts get-caller-identity                # Copy your account number for next step
$ cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```
3. Make sure `Docker Daemon` is running.
4. Synthesize cdk ```$ cdk synth```
5. Deploy cdk ```$ cdk deploy```
6. Invoke the lambda function ```$ aws lambda invoke --function-name user_tweets_producer out```

## Expected Outputs
Go into your AWS dashboard to view below expected outputs:

##### Cloudformation
There should be a stack called `TwitterApiStack` listed, which means that the cdk successfully built the app infrastructure.

##### Lambda functions
* user_tweets_producer - send tweet, media and meta events to queues (See SQS queues section below).
* tweets_consumer - receives events from tweet_queue, parse data and send data to twitter_user_tweets table.
* media_consumer - receives events from media_queue, parse data and send data to twitter-user-media bucket.
* meta_consumer - receives events from meta_queue, parse data and send data to tweet_meta_data table.

##### SQS queues
* tweet_queue - receives events from user_tweets_producer and triggers tweets_consumer.
* media_queue - receives events from user_tweets_producer and triggers media_consumer.
* meta_queue - receives events from user_tweets_producer and triggers meta_consumer.

##### DynamoDB tables
* twitter_user_tweets - this is where you will see user tweet data.
* tweet_meta_data - this is where you will find meta data on pagination for each user.

##### S3 bucket
* twitter-user-media - this is where user media data is stored.

##### Cloudwatch
Click on `log groups` on the left panel. There should be 4 lambda related log groups listed here.

## How To Change `TWIITER_USER_ID` and `TWITTER_BEARER_TOKEN`
1. Open `twitter_api_stack.py`.
2. Go to line 49 to change `TWITTER_BEARER_TOKEN` with your own bearer token.
3. Go to line 50 to change `TWIITER_USER_ID` with the desired user_id. Default is the user id of @nytimes.
4. Save changes.
5. Run diff on cdk ```$ cdk diff```
6. Deploy app ```$ cdk deploy```
7. Invoke the lambda function ```$ aws lambda invoke --function-name user_tweets_producer out```
8. Check tables and s3 buckets for results.

## Assumptions
* This app assumes that `TWIITER_USER_ID` AND `TWITTER_BEARER_TOKEN` in `twitter_api_stack.py` is supplied manually and hard coded in the code.
The `add_aws_lambda_envars.sh` is a way to do this from the command line.
* There are 3 keys returned from the response: `data`, `includes` and `meta`. 
The assumption is that this app will keep on requesting data until it reaches the rate limit. So, I decided to save `meta` data as well to keep track of pagination, in a separate table. I'm assuming that this app will be run every 15 minutes, so, the next time the app run, it can find the last page it left off. Function to handle this functionality is not implemented here. 
* The way data is stored in s3 and dynamodb tables are by no means perfect. I did not spend much time to analyze the data in order for me to come up with the best structure/model to store the data. 

