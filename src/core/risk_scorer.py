from enum import Enum
from dataclasses import dataclass
from typing import Optional

class RiskClassification(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class RiskSignals:
    qr_signature_valid: bool
    image_quality_score: float  # 0.0 to 1.0
    address_completeness: str  # COMPLETE, PARTIAL, MISSING
    photo_available: str       # AVAILABLE, FAILED, NOT_AVAILABLE
    liveness_passed: Optional[bool] = None

class RiskScoringEngine:
    def compute_score(self, signals: RiskSignals) -> tuple[int, RiskClassification]:
        score = 0
        
        # QR Signature Valid (35 pts)
        if not signals.qr_signature_valid:
            score += 35
            
        # Image Quality Score (20 pts)
        if signals.image_quality_score < 0.4:
            score += 20
        elif signals.image_quality_score < 0.7:
            # Linear penalty between 0.4 and 0.7
            score += int(20 * (0.7 - signals.image_quality_score) / 0.3)
            
        # Address Completeness (15 pts)
        if signals.address_completeness == "MISSING":
            score += 15
        elif signals.address_completeness == "PARTIAL":
            score += 8
            
        # Photo Availability (10 pts)
        if signals.photo_available == "FAILED":
            score += 10
        elif signals.photo_available == "NOT_AVAILABLE":
            score += 5
            
        # Liveness Result (20 pts)
        if signals.liveness_passed is False:
            score += 20
            
        # Classification
        if score <= 20:
            classification = RiskClassification.LOW
        elif score <= 45:
            classification = RiskClassification.MEDIUM
        else:
            classification = RiskClassification.HIGH
            
        return min(score, 100), classification
