import unittest
import os
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image


def create_test_image_bytes():
    """Create an in-memory JPEG image for testing."""
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


class TestLambdaFunction(unittest.TestCase):
    bucket_name = "test-bucket"

    @classmethod
    def setUpClass(cls):
        # Set environment variable before importing lambda_function
        os.environ["SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:TestTopic"
        global lf
        from src import lambda_function as lf

    @patch("src.lambda_function.detect_labels")
    @patch("src.lambda_function.draw_label_text")
    @patch("src.lambda_function.sns_publish")
    @patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:TestTopic"})
    def test_label_confidence_combined(self, mock_sns_publish, mock_draw_label_text, mock_detect_labels):
        mock_detect_labels.return_value = [
            {
                "Name": "TestObj",
                "Confidence": 88.5,
                "Instances": [{"BoundingBox": {"Left": 0, "Top": 0, "Width": 1, "Height": 1}}]
            }
        ]

        with patch("src.lambda_function.boto3.Session") as mock_boto_session:
            mock_s3 = MagicMock()
            mock_s3.get_object.return_value = {
                "Body": MagicMock(read=MagicMock(return_value=create_test_image_bytes().getvalue()))
            }

            mock_session_instance = MagicMock()
            mock_session_instance.client.return_value = mock_s3
            mock_boto_session.return_value = mock_session_instance

            event = {
                "Records": [{
                    "s3": {"bucket": {"name": self.bucket_name}, "object": {"key": "images/test.jpg"}}
                }]
            }

            result = lf.lambda_handler(event, None)

            self.assertEqual(result["statusCode"], 200)
            self.assertEqual(result["labels_detected"], 1)
            mock_draw_label_text.assert_called_once()
            mock_s3.get_object.assert_called_with(Bucket=self.bucket_name, Key="images/test.jpg")

    @patch("src.lambda_function.detect_labels")
    @patch("src.lambda_function.draw_bounding_boxes")
    @patch("src.lambda_function.sns_publish")
    def test_lambda_handler_draw_error(self, mock_sns_publish, mock_draw, mock_detect):
        mock_detect.return_value = [
            {
                "Name": "TestObject",
                "Confidence": 99.0,
                "Instances": [{"BoundingBox": {"Left": 0.1, "Top": 0.1, "Width": 0.5, "Height": 0.5}}]
            }
        ]
        mock_draw.side_effect = Exception("Drawing error")

        with patch("src.lambda_function.boto3.Session") as mock_boto_session:
            mock_s3 = MagicMock()
            mock_s3.get_object.return_value = {
                "Body": MagicMock(read=MagicMock(return_value=create_test_image_bytes().getvalue()))
            }

            mock_session_instance = MagicMock()
            mock_session_instance.client.return_value = mock_s3
            mock_boto_session.return_value = mock_session_instance

            event = {
                "Records": [{
                    "s3": {"bucket": {"name": self.bucket_name}, "object": {"key": "images/test.jpg"}}
                }]
            }

            result = lf.lambda_handler(event, None)

            self.assertEqual(result["statusCode"], 500)
            mock_sns_publish.assert_called_once()
            args, kwargs = mock_sns_publish.call_args
            subject = args[2] if len(args) > 2 else kwargs.get("subject", "")
            self.assertIn("Drawing Error", subject)

    @patch("src.lambda_function.detect_labels")
    @patch("src.lambda_function.sns_publish")
    def test_lambda_handler_no_labels(self, mock_sns_publish, mock_detect):
        mock_detect.return_value = []

        with patch("src.lambda_function.boto3.Session") as mock_boto_session:
            mock_s3 = MagicMock()
            mock_s3.get_object.return_value = {
                "Body": MagicMock(read=MagicMock(return_value=create_test_image_bytes().getvalue()))
            }

            mock_session_instance = MagicMock()
            mock_session_instance.client.return_value = mock_s3
            mock_boto_session.return_value = mock_session_instance

            event = {
                "Records": [{
                    "s3": {"bucket": {"name": self.bucket_name}, "object": {"key": "images/test.jpg"}}
                }]
            }

            result = lf.lambda_handler(event, None)

            self.assertEqual(result["statusCode"], 200)
            mock_sns_publish.assert_called_once()
            args, kwargs = mock_sns_publish.call_args
            subject = args[2] if len(args) > 2 else kwargs.get("subject", "")
            self.assertIn("Empty Results", subject)

    @patch("src.lambda_function.detect_labels")
    @patch("src.lambda_function.draw_bounding_boxes")
    @patch("src.lambda_function.draw_label_text")
    @patch("src.lambda_function.sns_publish")
    def test_lambda_handler_success(self, mock_sns_publish, mock_draw_label_text, mock_draw, mock_detect):
        mock_detect.return_value = [
            {
                "Name": "TestObject",
                "Confidence": 99.0,
                "Instances": [{"BoundingBox": {"Left": 0.1, "Top": 0.1, "Width": 0.5, "Height": 0.5}}]
            }
        ]

        with patch("src.lambda_function.boto3.Session") as mock_boto_session:
            mock_s3 = MagicMock()
            mock_s3.get_object.return_value = {
                "Body": MagicMock(read=MagicMock(return_value=create_test_image_bytes().getvalue()))
            }

            mock_session_instance = MagicMock()
            mock_session_instance.client.side_effect = lambda service_name, **kwargs: {
                "s3": mock_s3,
                "sns": MagicMock(publish=MagicMock(return_value={}))
            }[service_name]

            mock_boto_session.return_value = mock_session_instance

            event = {
                "Records": [{
                    "s3": {"bucket": {"name": self.bucket_name}, "object": {"key": "images/test.jpg"}}
                }]
            }

            result = lf.lambda_handler(event, None)

            self.assertEqual(result["statusCode"], 200)
            self.assertEqual(result["labels_detected"], 1)
            mock_draw.assert_called_once()
            mock_draw_label_text.assert_called_once()
