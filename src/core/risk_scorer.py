"""
Risk scoring engine — merged: user's linear interpolation for image quality
                               + mine's 6-signal weighted model + liveness weight fix.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class RiskClassification(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class RiskSignals:
    qr_signature_valid: bool
    image_quality_score: float       # 0.0–1.0
    address_completeness: str        # COMPLETE | PARTIAL | UNAVAILABLE
    photo_available: str             # AVAILABLE | NOT_AVAILABLE | FAILED
    data_completeness: float = 1.0   # 0.0–1.0 (name/dob/gender/uid all present)
    liveness_passed: Optional[bool] = None


class RiskScoringEngine:

    def compute_score(self, signals: RiskSignals):
        score = 0

        # QR Signature (35 pts)
        if not signals.qr_signature_valid:
            score += 35

        # Image Quality (20 pts) — linear penalty between 0.4 and 0.7
        iq = signals.image_quality_score
        if iq < 0.4:
            score += 20
        elif iq < 0.7:
            score += int(20 * (0.7 - iq) / 0.3)

        # Address Completeness (15 pts)
        if signals.address_completeness == "UNAVAILABLE":
            score += 15
        elif signals.address_completeness == "PARTIAL":
            score += 8

        # Data Completeness (10 pts)
        if signals.data_completeness < 0.5:
            score += 10
        elif signals.data_completeness < 0.8:
            score += 5

        # Photo (10 pts)
        if signals.photo_available == "FAILED":
            score += 10
        elif signals.photo_available == "NOT_AVAILABLE":
            score += 5

        # Liveness (10 pts)
        if signals.liveness_passed is False:
            score += 10

        score = min(score, 100)

        if score <= 20:
            cls = RiskClassification.LOW
        elif score <= 45:
            cls = RiskClassification.MEDIUM
        else:
            cls = RiskClassification.HIGH

        return score, cls
