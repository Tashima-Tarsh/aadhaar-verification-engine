import cv2
import numpy as np
from PIL import Image, ImageFilter
from deskew import determine_skew
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    def __init__(self, image: np.ndarray):
        self.image = image

    def to_grayscale(self) -> 'ImagePreprocessor':
        if len(self.image.shape) == 3:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return self

    def normalize_brightness(self) -> 'ImagePreprocessor':
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.image = clahe.apply(self.image)
        return self

    def reduce_noise(self) -> 'ImagePreprocessor':
        self.image = cv2.GaussianBlur(self.image, (3, 3), 0)
        self.image = cv2.fastNlMeansDenoising(self.image, None, 10, 7, 21)
        return self

    def adaptive_threshold(self) -> 'ImagePreprocessor':
        self.image = cv2.adaptiveThreshold(
            self.image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return self

    def sharpen_edges(self) -> 'ImagePreprocessor':
        pil_img = Image.fromarray(self.image)
        sharpened = pil_img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        self.image = np.array(sharpened)
        return self

    def detect_and_correct_rotation(self) -> 'ImagePreprocessor':
        angle = determine_skew(self.image)
        if angle:
            (h, w) = self.image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            self.image = cv2.warpAffine(
                self.image, M, (w, h), 
                flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
        return self

    def upscale_if_small(self, min_size: int = 800) -> 'ImagePreprocessor':
        h, w = self.image.shape[:2]
        if min(h, w) < min_size:
            scale = min_size / min(h, w)
            self.image = cv2.resize(
                self.image, None, fx=scale, fy=scale, 
                interpolation=cv2.INTER_CUBIC
            )
        return self

    def get_processed(self) -> np.ndarray:
        return self.image

def run_preprocessing_pipeline(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    preprocessor = ImagePreprocessor(image)
    return (
        preprocessor
        .to_grayscale()
        .normalize_brightness()
        .reduce_noise()
        .sharpen_edges()
        .detect_and_correct_rotation()
        .upscale_if_small()
        .get_processed()
    )
