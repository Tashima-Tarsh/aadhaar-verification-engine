"""
UIDAI Secure QR verifier — auto-detects V1 (plain XML) vs V2 (binary + RSA-SHA256).
"""
import zlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def verify_aadhaar_qr(raw_data: bytes) -> Dict[str, Any]:
    """Auto-detect QR version and verify."""
    if len(raw_data) > 2 and raw_data[0] == 0x78:  # zlib magic → V2
        return _verify_v2(raw_data)
    try:
        raw_data.decode("utf-8")
        return _verify_v1(raw_data)
    except UnicodeDecodeError:
        return _verify_v2(raw_data)


def _verify_v1(raw_data: bytes) -> Dict[str, Any]:
    from src.engines.document_processor import DocumentProcessor
    try:
        data = DocumentProcessor().process_xml(raw_data)
        data["signature_valid"] = False  # V1 has no digital signature
        data["qr_version"] = 1
        data["is_valid"] = True
        return data
    except Exception as e:
        return {"is_valid": False, "signature_valid": False, "qr_version": 1, "error": str(e)}


def _verify_v2(raw_data: bytes) -> Dict[str, Any]:
    from src.engines.signature_validator import SignatureValidator
    from src.config.settings import settings

    if len(raw_data) < 300:
        return {"is_valid": False, "signature_valid": False, "qr_version": 2, "error": "Data too short"}

    signature = raw_data[-256:]
    compressed = raw_data[:-256]

    try:
        validator = SignatureValidator(settings.UIDAI_PUBLIC_KEY_PATH)
        sig_valid, _ = validator.verify_signature(raw_data)
    except Exception:
        sig_valid = False

    try:
        xml_bytes = zlib.decompress(compressed)
        from src.engines.document_processor import DocumentProcessor
        data = DocumentProcessor().process_xml(xml_bytes)
        data["signature_valid"] = sig_valid
        data["qr_version"] = 2
        data["is_valid"] = sig_valid
        return data
    except Exception as e:
        return {"is_valid": False, "signature_valid": sig_valid, "qr_version": 2, "error": str(e)}
