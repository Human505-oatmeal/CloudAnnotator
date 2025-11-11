import logging
import time
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def retry(func, retries=2, delay=2):
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt < retries:
                logger.warning(f"Attempt {attempt} failed: {e}, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise

def sns_publish(session, topic_arn, subject, message):
    def publish():
        sns = session.client('sns')
        sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
    retry(publish)

def validate_aws_identity(session):
    sts = session.client("sts")
    try:
        identity = sts.get_caller_identity()
        logger.info(f"Running as AWS identity: {identity['Arn']}")
        return identity
    except Exception as e:
        logger.error(f"AWS identity validation failed: {e}")
        return None