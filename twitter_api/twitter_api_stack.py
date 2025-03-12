
from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb
)
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion
from aws_cdk.aws_lambda_event_sources import SqsEventSource


class TwitterApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------------------------------------------
        # Queues
        # ------------------------------------------------------------------------------------------------------
        tweet_q = sqs.Queue(self, "tweet_q", queue_name="tweet_queue", visibility_timeout=Duration.seconds(300))
        media_q = sqs.Queue(self, "media_q", queue_name="media_queue", visibility_timeout=Duration.seconds(300))
        meta_q = sqs.Queue(self, "meta_q", queue_name="meta_queue", visibility_timeout=Duration.seconds(300))

        # ------------------------------------------------------------------------------------------------------
        # Lambdas
        # ------------------------------------------------------------------------------------------------------
        python_layer = PythonLayerVersion(
            self,
            "python_layer",
            entry="lambdas",
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_10]
            )
        
        producer_lambda = PythonFunction(
            self,
            "producer_fn",
            function_name="user_tweets_producer",
            entry="lambdas",
            index="user_tweets_producer.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            timeout=Duration.seconds(6),
            layers=[python_layer],
            environment={
                "TWITTER_BEARER_TOKEN": "AAAAAAAAAAAAAAAAAAAA......", # Change this with your bearer token
                "TWITTER_USER_ID": "807095",                          # This is @nytimes twitter user ID, change it to other IDs you want
                "TWEET_QUEUE_URL": tweet_q.queue_url,
                "MEDIA_QUEUE_URL": media_q.queue_url,
                "META_QUEUE_URL": meta_q.queue_url,
                }
            )
        
        tweets_consumer = PythonFunction(
            self,
            "tweets_consumer",
            function_name="tweets_consumer",
            entry="lambdas",
            index="tweets_consumer.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[python_layer],
            environment={"DYNAMODB_TWEET_TABLE_NAME": "twitter_user_tweets"}
            )
        
        media_consumer = PythonFunction(
            self,
            "media_consumer",
            function_name="media_consumer",
            entry="lambdas",
            index="media_consumer.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[python_layer],
            environment={"S3_BUCKET_NAME": "twitter-user-media"}
            )
        
        meta_consumer = PythonFunction(
            self,
            "meta_consumer",
            function_name="meta_consumer",
            entry="lambdas",
            index="meta_consumer.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[python_layer],
            environment={"DYNAMODB_META_TABLE_NAME": "tweet_meta_data"}
            )

        # ------------------------------------------------------------------------------------------------------
        # Dynamodb
        # ------------------------------------------------------------------------------------------------------
        tweet_table = dynamodb.Table(
            self,
            "tweet_table",
            table_name="twitter_user_tweets",
            partition_key=dynamodb.Attribute(name="author_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="conversation_id", type=dynamodb.AttributeType.STRING)
            )

        meta_table = dynamodb.Table(
            self,
            "meta_table",
            table_name="tweet_meta_data",
            partition_key=dynamodb.Attribute(name="author_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="newest_id", type=dynamodb.AttributeType.STRING)
            )

        # ------------------------------------------------------------------------------------------------------
        # S3
        # ------------------------------------------------------------------------------------------------------
        media_bucket = s3.Bucket(
            self,
            "media_bucket",
            bucket_name="twitter-user-media"
            )
        
        # ------------------------------------------------------------------------------------------------------
        # IAM
        # ------------------------------------------------------------------------------------------------------
        # Grant producer_lambda permissions to send messages to tweet_q and media_q
        producer_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sqs:SendMessage",],
            resources=[tweet_q.queue_arn, media_q.queue_arn, meta_q.queue_arn],
            ))
        
        # ------------------------------------------------------------------------------------------------------
        # Grant tweets_consumer permissions to receive messages from tweet_q and write data to dynamoDB
        tweets_consumer.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ReceiveMessage"
            ],
            resources=[tweet_q.queue_arn]
        ))

        tweet_table.grant_read_write_data(tweets_consumer)        

        # ------------------------------------------------------------------------------------------------------
        # Grant media_consumer permissions to receive messages from media_q and write data to s3 bucket
        media_consumer.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ReceiveMessage"
            ],
            resources=[media_q.queue_arn]
        ))

        media_bucket.grant_read_write(media_consumer)

        # ------------------------------------------------------------------------------------------------------
        # Grant meta_consumer permissions to receive messages from meta_q and write data to dynamoDB
        meta_consumer.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ReceiveMessage"
            ],
            resources=[meta_q.queue_arn]
        ))

        meta_table.grant_read_write_data(meta_consumer)

        # ------------------------------------------------------------------------------------------------------
        # Connecting Services (Trigger lambda functions from SQS queues)
        # ------------------------------------------------------------------------------------------------------
        # tweet_q --> tweets_consumer
        tweet_sqs_source = SqsEventSource(tweet_q)
        tweets_consumer.add_event_source(tweet_sqs_source)
        # media_q --> media_consumer
        media_sqs_source = SqsEventSource(media_q)
        media_consumer.add_event_source(media_sqs_source)
        # meta_q --> meta_consumer
        meta_sqs_source = SqsEventSource(meta_q)
        meta_consumer.add_event_source(meta_sqs_source)

