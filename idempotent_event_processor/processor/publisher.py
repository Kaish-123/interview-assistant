import os
import boto3


def publish_event(event_id: str, detail: dict) -> None:
    """Publish a processed event notification to SNS."""
    import json

    sns = boto3.client("sns", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    sns.publish(
        TopicArn=topic_arn,
        Message=json.dumps({"event_id": event_id, "detail": detail}),
        Subject=f"DataRecordIngested: {event_id}",
    )
