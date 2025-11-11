import pytest
import boto3
import moto
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


# -----------------------------
# Test validate_aws_identity
# -----------------------------
@pytest.mark.usefixtures("mock_sts")
def test_validate_aws_identity():
    with moto.mock_sts():
        session = boto3.Session()
        identity = utils.validate_aws_identity(session)
        assert "Arn" in identity


# -----------------------------
# Test sns_publish
# -----------------------------
@pytest.mark.usefixtures("mock_sns")
def test_sns_publish():
    with moto.mock_sns():
        session = boto3.Session(region_name="us-east-2")
        sns = session.client("sns")
        topic = sns.create_topic(Name="TestTopic")["TopicArn"]

        # No exceptions thrown means success
        utils.sns_publish(session, topic, "Test Subject", "Test Message")
