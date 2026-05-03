import cv2
import numpy as np
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False
import zxingcpp
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class QRDecoderCascade:
    def __init__(self, image: np.ndarray):
        self.image = image

    def decode(self) -> Optional[bytes]:
        # Attempt 1: pyzbar default (if available)
        if PYZBAR_AVAILABLE:
            result = self._try_pyzbar(self.image)
            if result: return result

        # Attempt 2: zxing-cpp TryHarder
        result = self._try_zxing(self.image, try_harder=True)
        if result: return result

        # Attempt 3: Inverted image
        inverted = cv2.bitwise_not(self.image)
        if PYZBAR_AVAILABLE:
            result = self._try_pyzbar(inverted)
            if result: return result
        
        result = self._try_zxing(inverted, try_harder=True)
        if result: return result

        # Attempt 4: Multi-scale cascade
        for scale in [0.5, 1.5, 2.0]:
            h, w = self.image.shape[:2]
            resized = cv2.resize(self.image, (int(w * scale), int(h * scale)))
            result = self._try_zxing(resized)
            if result: return result

        # Attempt 5: Rotated variants
        for angle in [45, 135]:
            (h, w) = self.image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(self.image, M, (w, h))
            result = self._try_zxing(rotated)
            if result: return result

        return None

    def _try_pyzbar(self, img: np.ndarray) -> Optional[bytes]:
        try:
            decoded = pyzbar.decode(img)
            if decoded:
                return decoded[0].data
        except Exception as e:
            logger.error(f"pyzbar error: {e}")
        return None

    def _try_zxing(self, img: np.ndarray, try_harder: bool = False) -> Optional[bytes]:
        try:
            # Note: zxing-cpp read_barcodes takes images directly
            results = zxingcpp.read_barcodes(img)
            if results:
                return results[0].payload
        except Exception as e:
            logger.error(f"zxing error: {e}")
        return None

def decode_qr(image: np.ndarray) -> Optional[bytes]:
    cascade = QRDecoderCascade(image)
    return cascade.decode()
