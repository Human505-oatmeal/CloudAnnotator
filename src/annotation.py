from PIL import Image, ImageDraw, ImageFont
import os
import io
import tempfile
from datetime import datetime
from .utils import retry, logger

def draw_label_text(draw, text, position, bbox_width, bbox_height, img_height, fill='white', bg='red'):
    x, y = position
    font_path = "/opt/fonts/DejaVuSans-Bold.ttf"

    font_size = max(int(bbox_height * 0.5), int(img_height * 0.03), 12)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logger.warning(f"Font load failed, using default: {e}")
        font = ImageFont.load_default()

    bbox_text = draw.textbbox((0, 0), text, font=font)
    text_width = bbox_text[2] - bbox_text[0]
    text_height = bbox_text[3] - bbox_text[1]

    while text_width > bbox_width and font_size > 6:
        font_size -= 1
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
        bbox_text = draw.textbbox((0, 0), text, font=font)
        text_width = bbox_text[2] - bbox_text[0]
        text_height = bbox_text[3] - bbox_text[1]

    padding = 2
    rect_x0 = x
    rect_y0 = max(y - text_height - padding*2, 0)
    rect_x1 = x + text_width + padding*2
    rect_y1 = y
    draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=bg)

    ascent, _ = font.getmetrics()
    text_y = rect_y0 + padding - int(ascent * 0.15)
    draw.text((rect_x0 + padding, text_y), text, fill=fill, font=font)


def draw_bounding_boxes(bucket, photo, labels, session, min_confidence=70.0):
    s3 = session.client('s3')
    image_obj = retry(lambda: s3.get_object(Bucket=bucket, Key=photo))
    image = Image.open(io.BytesIO(image_obj['Body'].read()))
    img_width, img_height = image.size
    draw = ImageDraw.Draw(image)

    for label in labels:
        for instance in label.get('Instances', []):
            confidence = instance.get('Confidence', label.get('Confidence', 0.0))
            if confidence < min_confidence:
                continue

            box = instance['BoundingBox']
            left = img_width * box['Left']
            top = img_height * box['Top']
            width = img_width * box['Width']
            height = img_height * box['Height']

            draw.rectangle([left, top, left+width, top+height], outline='red', width=3)
            text_combined = f"{label['Name']} {confidence:.1f}%"
            draw_label_text(draw, text_combined, (left, top), width, height, img_height)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"annotated_{timestamp}_{os.path.basename(photo)}"


    temp_dir = tempfile.gettempdir()
    local_path = os.path.join(temp_dir, output_filename)

    image.save(local_path)
    s3.upload_file(local_path, bucket, f"annotated/{output_filename}")

    return local_path
