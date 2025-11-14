def detect_labels(bucket, key, session, max_labels=10, min_confidence=70):
    rekognition = session.client("rekognition", region_name="us-east-1")
    response = rekognition.detect_labels(
        Image={"S3Object": {"Bucket": bucket, "Name": key}},
        MaxLabels=max_labels,
        MinConfidence=min_confidence
    )
    return response.get("Labels", [])
