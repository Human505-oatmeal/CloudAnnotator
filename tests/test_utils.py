import pytest
import boto3
from moto import mock_aws  # use the new unified mock
from src import utils


def test_retry_success():
    call_count = {"count": 0}

    def func():
        call_count["count"] += 1
        return "ok"

    result = utils.retry(func, retries=3)
    assert result == "ok"
    assert call_count["count"] == 1


def test_retry_failure():
    call_count = {"count": 0}

    def func():
        call_count["count"] += 1
        raise ValueError("fail")

    with pytest.raises(ValueError):
        utils.retry(func, retries=2, delay=0.01)
    assert call_count["count"] == 2


def test_validate_aws_identity():
    with mock_aws(service="sts"):  # updated for Moto 5.x
        session = boto3.Session()
        identity = utils.validate_aws_identity(session)
        assert "Arn" in identity


def test_sns_publish():
    with mock_aws(service="sns"):  # updated for Moto 5.x
        session = boto3.Session(region_name="us-east-2")
        client = session.client("sns")
        topic_arn = client.create_topic(Name="TestTopic")["TopicArn"]

        # No exceptions thrown means success
        utils.sns_publish(session, topic_arn, "Test Subject", "Test Message")
