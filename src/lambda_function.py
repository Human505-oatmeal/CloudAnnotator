import os
import boto3
from io import BytesIO
from PIL import Image

from .annotation import draw_bounding_boxes, draw_label_text
from .utils import sns_publish


BUCKET_OUTPUT = os.environ.get("ANNOTATED_BUCKET", "annotated-bucket")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:region:acct:topic")


def detect_labels(bucket, key):
    rekognition = boto3.client("rekognition", region_name="us-east-1")

    response = rekognition.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        MaxLabels=10,
        MinConfidence=70,
    )
    return response.get("Labels", [])


def lambda_handler(event, context):
    s3 = boto3.client("s3", region_name="us-east-1")
    session = boto3.Session()  # create a session for utils/annotation functions

    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    labels = detect_labels(bucket, key)

    s3_obj = s3.get_object(Bucket=bucket, Key=key)
    image_bytes = s3_obj["Body"].read()
    image = Image.open(BytesIO(image_bytes))

    # Handle no labels detected
    if not labels:
        sns_publish(
            session,
            SNS_TOPIC_ARN,
            "Empty Results",                       # subject
            f"No labels detected in image {key}"   # message
        )
        return {"statusCode": 200, "message": "No labels detected"}

    try:
        # Draw bounding boxes using the bucket and key (photo)
        draw_bounding_boxes(bucket, key, labels, session=session)

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
        sns_publish(
            session,
            SNS_TOPIC_ARN,
            "Drawing Error",                         # subject
            f"Error drawing labels on image {key}: {str(e)}"  # message
        )
        return {"statusCode": 500, "error": str(e)}

    # Save annotated image
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    out_key = f"annotated/{os.path.basename(key)}"
    s3.put_object(
        Bucket=BUCKET_OUTPUT,
        Key=out_key,
        Body=buffer.getvalue(),
        ContentType="image/jpeg",
    )

    return {
        "statusCode": 200,
        "message": "Success",
        "labels_detected": len(labels),
    }
