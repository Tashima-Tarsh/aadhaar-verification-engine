import time
import logging
from typing import Dict, Any, Optional
from src.engines.preprocessing import run_preprocessing_pipeline
from src.engines.qr_decoder import decode_qr
from src.engines.signature_validator import SignatureValidator
from src.engines.address_normalizer import AddressNormalizer
from src.core.risk_scorer import RiskScoringEngine, RiskSignals
from src.config.settings import settings

logger = logging.getLogger(__name__)

class VerificationOrchestrator:
    def __init__(self):
        self.signature_validator = SignatureValidator(settings.UIDAI_PUBLIC_KEY_PATH)
        self.address_normalizer = AddressNormalizer()
        self.risk_scorer = RiskScoringEngine()

    async def verify_image(self, image_bytes: bytes) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Preprocessing
        processed_image = run_preprocessing_pipeline(image_bytes)
        
        # 2. QR Decoding
        qr_data = decode_qr(processed_image)
        if not qr_data:
            return self._error_response("ERR_INPUT_NO_QR_DETECTED", "No QR code detected in image", start_time)

        # 3. Signature Validation
        is_valid, signed_data = self.signature_validator.verify_signature(qr_data)
        if not is_valid:
            return self._error_response("ERR_QR_SIGNATURE_INVALID", "UIDAI digital signature verification failed", start_time)

        # 4. Data Extraction (Simplified for demo)
        # In real scenario, signed_data contains XML or encoded bytes
        extracted_data = self._parse_aadhaar_data(signed_data)
        
        # 5. Risk Scoring
        signals = RiskSignals(
            qr_signature_valid=True,
            image_quality_score=0.85, # Mock for now
            address_completeness="COMPLETE" if extracted_data.get('address') else "PARTIAL",
            photo_available="AVAILABLE" if extracted_data.get('photo') else "NOT_AVAILABLE",
            liveness_passed=None
        )
        risk_score, risk_class = self.risk_scorer.compute_score(signals)

        processing_time = int((time.time() - start_time) * 1000)

        return {
            "status": "COMPLETED",
            "qr_valid": True,
            "name": extracted_data.get('name'),
            "dob": extracted_data.get('dob'),
            "gender": extracted_data.get('gender'),
            "masked_aadhaar": self._mask_aadhaar(extracted_data.get('uid')),
            "photo_status": "AVAILABLE" if extracted_data.get('photo') else "NOT_AVAILABLE",
            "photo_data": extracted_data.get('photo'),
            "address": {
                "full": self.address_normalizer.normalize(extracted_data.get('address')),
                "state": self.address_normalizer.standardize_state(extracted_data.get('state')),
                "district": extracted_data.get('dist'),
                "pincode": self.address_normalizer.extract_pincode(extracted_data.get('address')),
                "status": "COMPLETE"
            },
            "risk_score": risk_class,
            "processing_time_ms": processing_time
        }

    def _parse_aadhaar_data(self, data: bytes) -> Dict[str, Any]:
        # Mock parser for demo
        # Real Aadhaar Secure QR uses a specific byte encoding
        return {
            "name": "John Doe",
            "dob": "1990-01-01",
            "gender": "M",
            "uid": "123456789012",
            "address": "Plot 15, Sector 4, New Delhi - 110001",
            "state": "Delhi",
            "dist": "New Delhi",
            "photo": "base64_encoded_photo_placeholder"
        }

    def _mask_aadhaar(self, uid: str) -> str:
        if not uid or len(uid) < 4:
            return "XXXX-XXXX-XXXX"
        return f"XXXX-XXXX-{uid[-4:]}"

    def _error_response(self, code: str, msg: str, start_time: float) -> Dict[str, Any]:
        return {
            "status": "FAILED",
            "error_code": code,
            "error_message": msg,
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
