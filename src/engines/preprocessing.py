"""
Image preprocessing pipeline.
Merged: user's fluent builder + deskew auto-rotation + PIL UnsharpMask,
        with CLAHE contrast enhancement and quality scoring from mine.
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter
import logging

logger = logging.getLogger(__name__)

try:
    from deskew import determine_skew
    DESKEW_AVAILABLE = True
except ImportError:
    DESKEW_AVAILABLE = False
    logger.warning("deskew not installed — auto-rotation disabled")


class ImagePreprocessor:
    def __init__(self, image: np.ndarray):
        self.image = image

    def to_grayscale(self) -> "ImagePreprocessor":
        if len(self.image.shape) == 3:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return self

    def normalize_brightness(self) -> "ImagePreprocessor":
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.image = clahe.apply(self.image)
        return self

    def reduce_noise(self) -> "ImagePreprocessor":
        self.image = cv2.GaussianBlur(self.image, (3, 3), 0)
        self.image = cv2.fastNlMeansDenoising(self.image, None, h=10, templateWindowSize=7, searchWindowSize=21)
        return self

    def adaptive_threshold(self) -> "ImagePreprocessor":
        self.image = cv2.adaptiveThreshold(
            self.image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return self

    def sharpen_edges(self) -> "ImagePreprocessor":
        pil_img = Image.fromarray(self.image)
        sharpened = pil_img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        self.image = np.array(sharpened)
        return self

    def detect_and_correct_rotation(self) -> "ImagePreprocessor":
        """Use deskew for continuous angle correction (handles non-90° tilts)."""
        if DESKEW_AVAILABLE:
            try:
                angle = determine_skew(self.image)
                if angle and abs(angle) > 0.5:
                    (h, w) = self.image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    self.image = cv2.warpAffine(
                        self.image, M, (w, h),
                        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                    )
            except Exception as e:
                logger.warning(f"deskew failed: {e}")
        return self

    def upscale_if_small(self, min_size: int = 800) -> "ImagePreprocessor":
        h, w = self.image.shape[:2]
        if min(h, w) < min_size:
            scale = min_size / min(h, w)
            self.image = cv2.resize(self.image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        return self

    def morphological_cleanup(self) -> "ImagePreprocessor":
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        self.image = cv2.morphologyEx(self.image, cv2.MORPH_CLOSE, kernel)
        return self

    def get_processed(self) -> np.ndarray:
        return self.image


def assess_quality(img: np.ndarray) -> float:
    gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = min(cv2.Laplacian(gray, cv2.CV_64F).var() / 500.0, 1.0)
    brightness = 1.0 - abs(gray.mean() - 128) / 128.0
    contrast = min(gray.std() / 64.0, 1.0)
    return round(sharpness * 0.5 + brightness * 0.25 + contrast * 0.25, 3)


def load_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        from PIL import Image as PILImage
        import io
        pil = PILImage.open(io.BytesIO(data)).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return img


def run_preprocessing_pipeline(image_bytes: bytes) -> np.ndarray:
    image = load_image(image_bytes)
    return (
        ImagePreprocessor(image)
        .to_grayscale()
        .normalize_brightness()
        .reduce_noise()
        .sharpen_edges()
        .detect_and_correct_rotation()
        .adaptive_threshold()
        .morphological_cleanup()
        .upscale_if_small()
        .get_processed()
    )


def rotate_image(img: np.ndarray, angle: int) -> np.ndarray:
    mapping = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    return cv2.rotate(img, mapping[angle]) if angle != 0 else img
