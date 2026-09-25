import cv2
import numpy as np

YUNET_MODEL = "attendance/models/face_detection_yunet_2023mar.onnx"
SFACE_MODEL = "attendance/models/face_recognition_sface_2021dec.onnx"

detector = cv2.FaceDetectorYN.create(
    YUNET_MODEL,
    "",
    (320, 320),
    0.9,
    0.3,
    5000
)

recognizer = cv2.FaceRecognizerSF_create(
    SFACE_MODEL,
    ""
)


def get_face_feature(image):
    """
    Image se face detect karke SFace embedding return karta hai.
    """
    if image is None:
        return None

    height, width = image.shape[:2]
    detector.setInputSize((width, height))

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        return None

    # Sabse bada face choose karo
    face = max(faces, key=lambda f: f[2] * f[3])

    try:
        aligned = recognizer.alignCrop(image, face)
        feature = recognizer.feature(aligned)
        return feature
    except Exception:
        return None


def compare_faces(feature1, feature2):
    """
    Cosine similarity return karta hai.
    Higher value = more similar.
    """
    return recognizer.match(
        feature1,
        feature2,
        cv2.FaceRecognizerSF_FR_COSINE
    )
