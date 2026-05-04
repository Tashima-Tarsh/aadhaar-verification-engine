"""
Liveness module — merged: user's Haar cascade (fast/lightweight) as primary,
                           DeepFace as enhanced option when LIVENESS_ENABLED=True.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class LivenessModule:

    def detect_face(self, image: np.ndarray) -> Tuple[bool, float]:
        """Returns (face_detected, confidence). Uses Haar cascade (no GPU needed)."""
        try:
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            if len(faces) > 0:
                return True, 0.85
        except Exception as e:
            logger.error(f"Face detection error: {e}")
        return False, 0.0

    def verify_liveness(
        self,
        selfie_bytes: bytes,
        document_photo_bytes: Optional[bytes] = None,
        use_deepface: bool = False,
    ) -> Tuple[bool, float]:
        """Returns (liveness_passed, confidence)."""
        arr = np.frombuffer(selfie_bytes, dtype=np.uint8)
        selfie_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if selfie_img is None:
            return False, 0.0

        face_detected, confidence = self.detect_face(selfie_img)
        if not face_detected:
            return False, 0.0

        if use_deepface and document_photo_bytes:
            try:
                from deepface import DeepFace
                arr2 = np.frombuffer(document_photo_bytes, dtype=np.uint8)
                doc_img = cv2.imdecode(arr2, cv2.IMREAD_COLOR)
                result = DeepFace.verify(
                    img1_path=selfie_img,
                    img2_path=doc_img,
                    model_name="VGG-Face",
                    enforce_detection=False,
                )
                match = result.get("verified", False)
                dist = result.get("distance", 1.0)
                return match, round(1.0 - dist, 3)
            except Exception as e:
                logger.warning(f"DeepFace verification failed: {e}")

        return True, confidence
