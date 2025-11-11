import pytest
from unittest.mock import MagicMock
import boto3
from moto import mock_sns, mock_sts
import os
import time

from src import utils

# -----------------------------
# Test retry decorator
# -----------------------------
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
@mock_sts
def test_validate_aws_identity():
    session = boto3.Session()
    identity = utils.validate_aws_identity(session)
    # Should return dict containing 'Arn'
    assert "Arn" in identity

# -----------------------------
# Test sns_publish
# -----------------------------
@mock_sns
def test_sns_publish():
    session = boto3.Session(region_name="us-east-2")
    sns = session.client("sns")
    topic = sns.create_topic(Name="TestTopic")["TopicArn"]

    utils.sns_publish(session, topic, "Test Subject", "Test Message")
    # No exceptions thrown means success
