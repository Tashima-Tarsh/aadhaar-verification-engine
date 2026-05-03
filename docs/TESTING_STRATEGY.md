# Testing Strategy — Aadhaar Verification Platform

The platform enforces a multi-tier testing strategy to ensure reliability, security, and performance under peak loads.

---

## 1. Unit Testing
Focuses on pure functions, especially in the `engines/` and `core/` layers.

### [Python Example] — `tests/unit/test_risk_scorer.py`
```python
import pytest
from src.core.risk_scorer import RiskScorer

def test_risk_scorer_low_risk():
    scorer = RiskScorer()
    # High quality, valid signature, complete address
    score, classification = scorer.calculate(
        qr_valid=True,
        quality_score=0.9,
        address_complete=True
    )
    assert score < 20
    assert classification == "LOW"

def test_risk_scorer_high_risk_invalid_sig():
    scorer = RiskScorer()
    score, classification = scorer.calculate(
        qr_valid=False,
        quality_score=0.8,
        address_complete=True
    )
    assert classification == "HIGH"
```

---

## 2. Integration Testing
Validates the interaction between the API, Database, and Workers using **Testcontainers**.

### Flow:
1. **Setup**: Spin up Postgres and Redis containers.
2. **Action**: Submit a `/verify` request with a sample Aadhaar image.
3. **Assertion**: Verify that a record is created in `verification_requests` and `verification_results` within the database.
4. **Cleanup**: Teardown containers.

---

## 3. Load Testing Approach
The platform is designed to handle **5,000 requests/day** with bursts of **200 requests/minute**.

### Tool: Locust
We use Locust to simulate multiple CRM systems submitting requests concurrently.

**Performance Targets**:
- **P95 Latency (Sync API)**: < 200ms (Request ingestion)
- **P95 Latency (Async Worker)**: < 5s (Full image processing to Webhook)
- **Error Rate**: < 0.1% at 50 concurrent users.

---

## 4. Security Testing
- **OWASP ZAP**: Automated scanning for API vulnerabilities.
- **Burp Suite**: Manual testing for IDOR (Insecure Direct Object Reference) on the results endpoints.
- **Payload Fuzzing**: Testing the engines with corrupted PDF and malformed XML files.
