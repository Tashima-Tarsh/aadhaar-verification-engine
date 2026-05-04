"""
VerificationOrchestrator — full 7-stage pipeline (no mock data).
Stage 1: Image Preprocessing
Stage 2: QR Detection & Decode
Stage 3: Signature Validation
Stage 4: Data Extraction (XML/PDF/ZIP)
Stage 5: Photo Extraction
Stage 6: Address Normalization
Stage 7: Risk Scoring
"""
import time
import logging
from typing import Dict, Any, Optional

from src.engines.preprocessing import run_preprocessing_pipeline, assess_quality, load_image
from src.engines.qr_decoder import decode_qr
from src.engines.signature_validator import SignatureValidator
from src.engines.aadhaar_verifier import verify_aadhaar_qr
from src.engines.address_normalizer import AddressNormalizer
from src.core.risk_scorer import RiskScoringEngine, RiskSignals
from src.config.settings import settings

logger = logging.getLogger(__name__)


class VerificationOrchestrator:
    def __init__(self):
        self.signature_validator = SignatureValidator(settings.UIDAI_PUBLIC_KEY_PATH)
        self.address_normalizer = AddressNormalizer()
        self.risk_scorer = RiskScoringEngine()

    async def verify_image(self, image_bytes: bytes, selfie_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        start = time.time()

        # Stage 1: quality assessment + preprocessing
        raw_img = load_image(image_bytes)
        quality = assess_quality(raw_img)
        processed = run_preprocessing_pipeline(image_bytes)

        # Stage 2: QR decode
        qr_data = decode_qr(processed)
        if not qr_data:
            return self._error("ERR_QR_NOT_DETECTED", "No QR code detected in image", start, quality)

        # Stage 3 + 4: Verify + extract via Aadhaar verifier (handles V1/V2)
        data = verify_aadhaar_qr(qr_data)
        if not data or data.get("error"):
            return self._error("ERR_QR_PARSE_FAILED", data.get("error", "QR parsing failed"), start, quality)

        sig_valid = data.get("signature_valid", False)

        # Stage 5: Photo extraction
        photo_bytes = data.get("photo")
        photo_status = "AVAILABLE" if photo_bytes else "NOT_AVAILABLE"

        # Stage 6: Address normalization
        raw_addr = data.get("address") or {}
        addr = self.address_normalizer.normalize_full(raw_addr)

        # Liveness (optional)
        liveness_passed = None
        liveness_conf = None
        if settings.LIVENESS_ENABLED and selfie_bytes:
            from src.core.liveness import LivenessModule
            module = LivenessModule()
            liveness_passed, liveness_conf = module.verify_liveness(
                selfie_bytes, photo_bytes, use_deepface=True
            )

        # Data completeness
        fields = [data.get("name"), data.get("dob"), data.get("gender"), data.get("masked_uid")]
        data_completeness = sum(1 for f in fields if f) / len(fields)

        # Stage 7: Risk scoring
        signals = RiskSignals(
            qr_signature_valid=sig_valid,
            image_quality_score=quality,
            address_completeness=addr.status,
            photo_available=photo_status,
            data_completeness=data_completeness,
            liveness_passed=liveness_passed,
        )
        risk_score, risk_class = self.risk_scorer.compute_score(signals)

        return {
            "status": "COMPLETED",
            "qr_valid": sig_valid,
            "qr_version": data.get("qr_version", 2),
            "name": data.get("name"),
            "dob": data.get("dob"),
            "gender": data.get("gender"),
            "masked_aadhaar": data.get("masked_uid"),
            "photo_status": photo_status,
            "photo_data": photo_bytes,
            "address": {
                "full": addr.full,
                "house": addr.house,
                "street": addr.street,
                "landmark": addr.landmark,
                "city": addr.city,
                "district": addr.district,
                "state": addr.state,
                "pincode": addr.pincode,
                "status": addr.status,
            },
            "risk_score": risk_class.value,
            "risk_numeric": risk_score,
            "liveness_result": "PASS" if liveness_passed else ("FAIL" if liveness_passed is False else "NOT_APPLICABLE"),
            "liveness_confidence": liveness_conf,
            "image_quality_score": quality,
            "processing_time_ms": int((time.time() - start) * 1000),
        }

    async def verify_document(
        self, file_bytes: bytes, source_type: str,
        password: Optional[str] = None,
        selfie_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Route to correct verifier based on source_type."""
        start = time.time()

        if source_type == "IMAGE":
            return await self.verify_image(file_bytes, selfie_bytes)

        from src.engines.document_processor import DocumentProcessor
        dp = DocumentProcessor()
        try:
            if source_type == "PDF":
                data = dp.process_pdf(file_bytes, password or "")
            elif source_type == "XML":
                data = dp.process_zip(file_bytes, password or "")
            else:
                return self._error("ERR_UNKNOWN_TYPE", f"Unsupported source_type: {source_type}", start)
        except ValueError as e:
            return self._error("ERR_DOCUMENT_DECRYPT", str(e), start)

        # Reuse image verify flow but with already-extracted data
        sig_valid = data.get("signature_valid", False)
        photo_bytes = data.get("photo")
        raw_addr = data.get("address") or {}
        addr = self.address_normalizer.normalize_full(raw_addr)

        liveness_passed = None
        if settings.LIVENESS_ENABLED and selfie_bytes and photo_bytes:
            from src.core.liveness import LivenessModule
            liveness_passed, _ = LivenessModule().verify_liveness(selfie_bytes, photo_bytes, use_deepface=True)

        fields = [data.get("name"), data.get("dob"), data.get("gender"), data.get("masked_uid")]
        data_completeness = sum(1 for f in fields if f) / len(fields)

        signals = RiskSignals(
            qr_signature_valid=sig_valid,
            image_quality_score=1.0,
            address_completeness=addr.status,
            photo_available="AVAILABLE" if photo_bytes else "NOT_AVAILABLE",
            data_completeness=data_completeness,
            liveness_passed=liveness_passed,
        )
        risk_score, risk_class = self.risk_scorer.compute_score(signals)

        return {
            "status": "COMPLETED",
            "qr_valid": sig_valid,
            "name": data.get("name"),
            "dob": data.get("dob"),
            "gender": data.get("gender"),
            "masked_aadhaar": data.get("masked_uid"),
            "photo_status": "AVAILABLE" if photo_bytes else "NOT_AVAILABLE",
            "photo_data": photo_bytes,
            "address": {"full": addr.full, "district": addr.district, "state": addr.state, "pincode": addr.pincode, "status": addr.status},
            "risk_score": risk_class.value,
            "risk_numeric": risk_score,
            "liveness_result": "PASS" if liveness_passed else ("FAIL" if liveness_passed is False else "NOT_APPLICABLE"),
            "image_quality_score": 1.0,
            "processing_time_ms": int((time.time() - start) * 1000),
        }

    def _error(self, code: str, msg: str, start: float, quality: float = 0.0) -> Dict[str, Any]:
        return {
            "status": "FAILED",
            "error_code": code,
            "error_message": msg,
            "image_quality_score": quality,
            "processing_time_ms": int((time.time() - start) * 1000),
        }
