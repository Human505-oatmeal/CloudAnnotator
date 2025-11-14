import os
import boto3
from io import BytesIO
from PIL import Image

from .annotation import draw_bounding_boxes, draw_label_text
from .utils import sns_publish, validate_aws_identity, retry

# Environment variables
BUCKET_OUTPUT = os.environ.get("ANNOTATED_BUCKET", "annotated-bucket")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", 70.0))
MAX_LABELS = int(os.environ.get("MAX_LABELS", 10))


def detect_labels(bucket, key, session):
    rekognition = session.client("rekognition", region_name="us-east-1")
    try:
        response = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=MAX_LABELS,
            MinConfidence=CONFIDENCE_THRESHOLD
        )
        return response.get("Labels", [])
    except Exception as e:
        raise RuntimeError(f"Rekognition detect_labels failed: {e}")


def lambda_handler(event, context):
    if not SNS_TOPIC_ARN:
        raise RuntimeError("SNS_TOPIC_ARN environment variable is required")

    session = boto3.Session()
    validate_aws_identity(session)

    s3 = session.client("s3", region_name="us-east-1")
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    # Detect labels
    try:
        labels = detect_labels(bucket, key, session)
    except Exception as e:
        sns_publish(session, SNS_TOPIC_ARN, "Rekognition Error", f"Error detecting labels: {e}")
        return {"statusCode": 500, "error": str(e)}

    # Handle no labels
    if not labels:
        sns_publish(session, SNS_TOPIC_ARN, "Empty Results", f"No labels detected in image {key}")
        return {"statusCode": 200, "message": "No labels detected"}

    # Fetch image bytes
    image_obj = retry(lambda: s3.get_object(Bucket=bucket, Key=key))
    image = Image.open(BytesIO(image_obj["Body"].read()))

    # Draw bounding boxes
    try:
        draw_bounding_boxes(bucket, key, labels, session=session, min_confidence=CONFIDENCE_THRESHOLD)

        # Optional: overlay labels on image in memory
        for label in labels:
            name = label["Name"]
            conf = label["Confidence"]
            draw_label_text(
                image,
                f"{name}: {conf:.2f}",
                position=(0, 0),
                bbox_width=100,
                bbox_height=100,
                img_height=int(image.height)
            )
    except Exception as e:
        sns_publish(session, SNS_TOPIC_ARN, "Drawing Error", f"Error drawing labels on image {key}: {e}")
        return {"statusCode": 500, "error": str(e)}

    # Save annotated image to S3
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    out_key = f"annotated/{os.path.basename(key)}"
    s3.put_object(
        Bucket=BUCKET_OUTPUT,
        Key=out_key,
        Body=buffer.getvalue(),
        ContentType="image/jpeg"
    )

    return {"statusCode": 200, "message": "Success", "labels_detected": len(labels)}
