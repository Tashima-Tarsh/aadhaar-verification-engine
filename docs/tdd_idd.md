# AADHAAR OFFLINE VERIFICATION
## RISK & IDENTITY INTELLIGENCE PLATFORM
### Technical Design Document (TDD) & Implementation Design Document (IDD)

**Document Version**: v1.0.0 — FINAL  
**Classification**: CONFIDENTIAL — INTERNAL ONLY  
**Document Type**: TDD + IDD (Combined Enterprise Specification)  
**Target Stack**: Python 3.11+, FastAPI, PostgreSQL, Redis, Docker  
**Compliance**: UIDAI Offline Verification Guidelines  
**Author**: Platform Engineering — FinTech Division  
**Status**: APPROVED FOR DEVELOPMENT

---

## 1. Executive Overview
This document defines the engineering specification for the Aadhaar Offline Verification Platform, built for high-volume, compliant identity verification.

### 1.2 Platform Mission
- Processes degraded inputs (B/W, blurred, rotated).
- Handles >= 5,000 verifications/day.
- Extracts photo, demographic, and address data.
- Produces risk intelligence scores.
- Zero online Aadhaar API calls (Full Offline Compliance).

---

## 2. System Architecture
### 2.1 Architecture Style
Layered, service-oriented architecture:
- **API Gateway**: FastAPI + Pydantic v2.
- **Domain Service**: Business logic orchestration.
- **Verification Engine**: QR decoding, XML/PDF processing.
- **Worker/Queue**: Celery + Redis for bulk processing.
- **Data Layer**: PostgreSQL + Redis + S3/MinIO.

### 2.2 Project Structure
```text
src/
├── api/             # FastAPI routers and schemas
├── core/            # Business logic (Orchestrator, Risk Scorer)
├── engines/         # QR, XML, PDF, Image processing engines
├── workers/         # Celery tasks
├── db/              # Models, Repositories, Migrations
├── services/        # Orchestration services
├── config/          # Environment-based configuration
└── utils/           # Shared utilities
tests/               # Unit, Integration, E2E tests
docker/              # Containerization files
```

---

## 3. Database Design (PostgreSQL)
- **Tables**: `verification_requests`, `verification_results`, `bulk_jobs`, `audit_logs`.
- **Principles**: UUID PKs, TIMESTAMPTZ, masked Aadhaar, application-layer encryption for photos.

---

## 4. API Specification
- **POST /api/v1/verify**: Single verification.
- **POST /api/v1/bulk/upload**: Async batch upload.
- **GET /api/v1/bulk/{job_id}/status**: Job progress.
- **GET /api/v1/verify/{request_id}**: Retrieve results.

---

## 5. Verification Engine
- **Preprocessing**: Grayscale, CLAHE, Denoising, Deskew, Upscaling.
- **QR Decoding**: Multi-library cascade (pyzbar -> zxing-cpp).
- **Signature Validation**: RSA-SHA256 against UIDAI public key.
- **Address Normalization**: Regex-based cleaning and standardization.

---

## 6. Testing Strategy
- **Target**: >= 90% coverage.
- **Stack**: pytest, pytest-asyncio, Testcontainers, Locust, Bandit.
- **Categories**: Unit, Integration, E2E, Performance, Security.

---

## 7. Compliance & Security
- **Data Retention**: 90 days for records, 30 days for photos, 24 hours for source files.
- **Encryption**: AES-256 for storage, Fernet for DB fields, TLS 1.3 for transit.
- **UIDAI Compliance**: No online calls, Aadhaar masking, audit trails.
