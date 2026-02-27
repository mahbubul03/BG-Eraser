# processor.py
from PIL import Image
import cv2
import numpy as np
from rembg import remove


def process_image(file_path: str) -> tuple[Image.Image, bool]:
    """
    Remove background using rembg and automatically crop to the largest face (if detected).
    Returns (final_image, face_was_detected)
    """
    # Load and remove background
    inp = Image.open(file_path)
    removed = remove(inp)

    face_detected = False
    final_image = removed

    try:
        # Face detection on the background-removed image
        rgb = removed.convert("RGB")
        opencv_img = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            # Use largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

            # 25% horizontal / 30% vertical padding
            pad_w = int(w * 0.25)
            pad_h = int(h * 0.30)

            left   = max(0, x - pad_w)
            top    = max(0, y - pad_h)
            right  = min(removed.width,  x + w + pad_w)
            bottom = min(removed.height, y + h + pad_h)

            final_image = removed.crop((left, top, right, bottom))
            face_detected = True

    except Exception:
        # Face detection failed → fallback to full background-removed image
        pass

    return final_image, face_detected