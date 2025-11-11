import pytest
from PIL import Image, ImageDraw
from src import annotation
import io

# -----------------------------
# Test draw_label_text
# -----------------------------
def test_draw_label_text_runs():
    img = Image.new("RGB", (200, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Just ensure it runs without error
    annotation.draw_label_text(
        draw,
        text="Hello 99%",
        position=(10, 50),
        bbox_width=100,
        bbox_height=50,
        img_height=200
    )

def test_draw_bounding_boxes_runs(monkeypatch):
    # Mock boto3 s3 client
    class MockS3:
        def get_object(self, Bucket, Key):
            img = Image.new("RGB", (100, 100), color="blue")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            return {"Body": buf}

        def upload_file(self, Filename, Bucket, Key):
            return True

    class MockSession:
        def client(self, service):
            return MockS3()

    # Sample labels
    labels = [
        {"Name": "TestObj", "Confidence": 90.0,
         "Instances": [{"BoundingBox": {"Left": 0, "Top": 0, "Width": 1, "Height": 1}}]}
    ]

    session = MockSession()
    annotation.draw_bounding_boxes(
        bucket="test-bucket",
        photo="test.jpg",
        labels=labels,
        session=session,
        min_confidence=50.0
    )
