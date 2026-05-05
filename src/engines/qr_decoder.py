"""
Multi-strategy QR decoder.
Merged: user's zxing-cpp + inverted image + 45/135° rotation
        + mine: pyzbar, QReader(ML), 4-cardinal rotations, multi-scale.
Strategy order: pyzbar → zxing TryHarder → inverted → multi-scale → ML(QReader)
"""
import cv2
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

try:
    import zxingcpp
    ZXING_AVAILABLE = True
except Exception:
    ZXING_AVAILABLE = False

CARDINAL_ANGLES = [0, 90, 180, 270]
DIAGONAL_ANGLES = [45, 135]


def _try_pyzbar(img: np.ndarray) -> Optional[bytes]:
    if not PYZBAR_AVAILABLE:
        return None
    try:
        decoded = pyzbar.decode(img)
        for d in decoded:
            if d.type == "QRCODE":
                return d.data
    except Exception as e:
        logger.debug(f"pyzbar: {e}")
    return None


def _try_zxing(img: np.ndarray, try_harder: bool = True) -> Optional[bytes]:
    if not ZXING_AVAILABLE:
        return None
    try:
        hints = zxingcpp.DecodeHints()
        if try_harder:
            hints.try_harder = True
        results = zxingcpp.read_barcodes(img, hints)
        if results:
            payload = results[0].text
            return payload.encode() if isinstance(payload, str) else payload
    except Exception as e:
        logger.debug(f"zxing: {e}")
    return None


def _try_qreader(img: np.ndarray) -> Optional[bytes]:
    try:
        from qreader import QReader
        rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = QReader().detect_and_decode(image=rgb)
        if result and result[0]:
            return result[0].encode()
    except Exception as e:
        logger.debug(f"qreader: {e}")
    return None


def _rotate(img: np.ndarray, angle: int) -> np.ndarray:
    if angle == 0:
        return img
    if angle in (90, 180, 270):
        m = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
        return cv2.rotate(img, m[angle])
    # Arbitrary angle (45°, 135°)
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h))


def _try_all_strategies(img: np.ndarray) -> Optional[bytes]:
    result = _try_pyzbar(img)
    if result:
        return result
    result = _try_zxing(img, try_harder=True)
    if result:
        return result
    # Inverted image (handles light-on-dark QRs)
    inverted = cv2.bitwise_not(img)
    result = _try_pyzbar(inverted) or _try_zxing(inverted, try_harder=True)
    if result:
        return result
    return None


def decode_qr(image) -> Optional[bytes]:
    """
    Full cascade: cardinal rotations → multi-scale → diagonal → ML fallback.
    Accepts a preprocessed grayscale np.ndarray or raw image bytes.
    """
    if isinstance(image, (bytes, bytearray)):
        arr = np.frombuffer(image, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return None
    # 1. Cardinal rotations (0°, 90°, 180°, 270°) at original scale
    for angle in CARDINAL_ANGLES:
        rotated = _rotate(image, angle)
        result = _try_all_strategies(rotated)
        if result:
            return result

    # 2. Multi-scale (0.5x, 1.5x, 2x) at 0° only
    h, w = image.shape[:2]
    for scale in [0.5, 1.5, 2.0]:
        scaled = cv2.resize(image, (int(w * scale), int(h * scale)),
                            interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
        result = _try_all_strategies(scaled)
        if result:
            return result

    # 3. Diagonal rotations (45°, 135°)
    for angle in DIAGONAL_ANGLES:
        rotated = _rotate(image, angle)
        result = _try_all_strategies(rotated)
        if result:
            return result

    # 4. ML-based QReader — last resort (slowest, handles severely damaged QRs)
    result = _try_qreader(image)
    if result:
        return result

    logger.warning("qr_decode_failed_all_strategies")
    return None
