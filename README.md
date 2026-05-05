# Aadhaar Offline Verification, Risk & Identity Intelligence Platform

> **Enterprise identity infrastructure for regulated financial institutions — built offline-first, designed for scale, architected for compliance.**

---

## What This Platform Is

This is a **production-ready identity verification engine** purpose-built for fintech, NBFC, microfinance, insurance, and lending institutions operating in the Indian regulatory environment.

The platform enables any enterprise system — CRM, LOS, onboarding portal, or mobile app — to verify Aadhaar identity in real time, without ever transmitting citizen data to UIDAI or any external server. Every verification happens entirely inside your own infrastructure boundary.

It is not a wrapper around a third-party API. It is a full-stack, self-contained identity intelligence engine.

---

## What It Achieves

| Business Objective | How the Platform Delivers |
|---|---|
| Regulatory compliance (DPDP Act, IT Act, UIDAI Offline KYC guidelines) | 100% offline — zero data egress to UIDAI or any third party |
| KYC automation at scale | Async queue processes 5,000+ documents per day per worker cluster |
| Fraud prevention | Cryptographic QR signature verification + 6-signal weighted risk scoring |
| CRM / LOS integration | REST API + HMAC-signed webhook callbacks + presigned S3 URLs for direct upload |
| Full auditability | Immutable audit log for every verification event with timestamps |
| Multi-tenant SaaS operations | API-key and JWT auth per tenant with isolated data boundaries |
| Operational visibility | Operator dashboard with live stats, risk distribution, and CSV export |

---

## Technology Stack

### Core Platform

| Layer | Technology | Purpose |
|---|---|---|
| API Framework | FastAPI 0.111 + Uvicorn | High-throughput async REST API with OpenAPI docs |
| Language | Python 3.11 | Fully async, type-safe |
| Database | PostgreSQL 15 + asyncpg | Immutable verification records + audit logs |
| ORM | SQLAlchemy 2.0 (async) | Repository pattern, connection pooling |
| Schema Validation | Pydantic v2 | Strict request/response contracts |
| DB Migrations | Alembic | Zero-downtime schema versioning |

### Document Intelligence

| Component | Technology | Capability |
|---|---|---|
| Image Preprocessing | OpenCV + Pillow + scikit-image + deskew | CLAHE contrast enhancement, auto-deskew, denoising, morphological cleanup |
| QR Decoding | pyzbar + zxing-cpp + QReader ML | Multi-engine cascade — handles blurred, rotated, cropped, low-resolution QR codes |
| PDF Processing | PyMuPDF + pikepdf | Password-protected eAadhaar PDF decrypt + QR frame extraction |
| XML Processing | pyzipper + lxml | AES-256 eAadhaar ZIP decrypt + XXE-safe XML parsing |
| Signature Validation | cryptography (RSA-SHA256) | UIDAI public key offline signature verification — V1 and V2 QR formats |
| Address Intelligence | Custom normalizer | State abbreviation resolution, pincode validation, completeness scoring |
| Liveness Detection | DeepFace + OpenCV Haar cascade | Optional face match between selfie and document photo |

### Infrastructure

| Component | Technology | Purpose |
|---|---|---|
| Task Queue | Celery 5 + Redis | Async verification, exponential retry, Dead Letter Queue |
| Object Storage | MinIO / AWS S3 | Document storage with presigned upload + download URLs |
| Auth | JWT (python-jose) + API Key (HMAC-SHA256) | Dual-mode tenant authentication |
| Encryption | Fernet (AES-128-CBC) | Field-level encryption for document passwords at rest |
| Webhook Signing | HMAC-SHA256 (X-Hub-Signature-256) | Tamper-proof CRM/LOS callbacks |
| Automation | n8n | Success / failure / high-risk escalation workflow triggers |
| Frontend | Next.js 14 + Tailwind CSS + Recharts + TanStack Query | Operator dashboard with live polling |
| Logging | structlog + Sentry | Structured JSON logs + error tracking with full context |
| Containers | Docker + Docker Compose | Reproducible full-stack deployment |

---

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT SYSTEMS                           │
│          CRM  │  LOS  │  Mobile App  │  Onboarding Portal      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API  /  Presigned S3 Upload
┌──────────────────────────▼──────────────────────────────────────┐
│                     API GATEWAY  (FastAPI)                       │
│  /api/v1/verify  │  /api/v1/batch  │  /api/v1/auth  │  /health  │
│        JWT + API Key Auth  │  Rate Limiting  │  Request ID       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────▼────────────────┐
          │     CELERY TASK QUEUE (Redis)    │
          │   aadhaar_verification queue     │
          │   aadhaar_dlq  (dead letter)     │
          └────────────────┬────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    VERIFICATION ENGINE                           │
│                                                                  │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │ Preprocessor │→ │ QR Decoder  │→ │  Signature Validator   │ │
│  │ CLAHE+deskew │  │  3-lib      │  │  UIDAI RSA-SHA256      │ │
│  └──────────────┘  │  cascade    │  └────────────────────────┘ │
│                    └─────────────┘                              │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │  Doc Parser  │  │ Risk Scorer │  │  Liveness  (optional)  │ │
│  │  PDF/XML/ZIP │  │  6-signal   │  │  DeepFace + Haar       │ │
│  └──────────────┘  └─────────────┘  └────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
     ┌─────────────────────▼─────────────────────┐
     │           DATA PERSISTENCE                  │
     │   PostgreSQL (records + audit logs)          │
     │   MinIO / S3 (document store)               │
     └─────────────────────┬─────────────────────┘
                           │  Webhook  (HMAC-signed)
     ┌─────────────────────▼─────────────────────┐
     │      CRM CALLBACK  +  n8n WORKFLOWS        │
     │   Success  │  Failure  │  High-Risk Alert  │
     └────────────────────────────────────────────┘
```

---

## Plug-In / Plug-Out Module Design

The platform is architected as **independently toggleable modules**. Every component beyond the core engine is optional. Enable exactly what your deployment requires — nothing more.

### Module Registry

| Module | Default State | How to Toggle | External Dependency |
|---|---|---|---|
| Core Verification (QR / PDF / XML) | Always On | Cannot be disabled — this is the engine | None |
| Bulk Processing (Celery workers) | On | Omit worker service from compose | Redis |
| Liveness Detection | Off | `LIVENESS_ENABLED=true` + install extra | None (bundled model) |
| Webhook Callbacks | Off | Set `webhook_url` on tenant record | Your HTTP endpoint |
| n8n Workflow Automation | Off | Start `n8n` compose service | n8n container |
| MinIO (local object storage) | On | Point to AWS S3 via env vars | AWS credentials |
| Frontend Dashboard | Off | Start `frontend` compose service | Node 18 |
| Sentry Error Tracking | Off | Set `SENTRY_DSN` env var | Sentry DSN |

### Enabling a Module

**Liveness Detection** — face match between selfie and document photo:
```bash
pip install ".[liveness]"    # installs deepface + tf-keras
# then in .env:
LIVENESS_ENABLED=true
```

**Webhook Callbacks** — per-tenant HMAC-signed HTTP callbacks to your CRM:
```bash
POST /api/v1/tenants
{
  "name": "MyOrg",
  "webhook_url": "https://your-crm.com/aadhaar/callback",
  "webhook_secret": "your-32-char-hmac-secret"
}
```
Every completed verification POSTs a signed payload to that URL with header `X-Hub-Signature-256`.

**n8n Automation** — trigger workflows on success, failure, or high-risk:
```bash
docker compose up n8n
# Workflows auto-load from n8n/workflows/:
#   workflow_success.json    — on COMPLETED
#   workflow_failure.json    — on FAILED
#   workflow_high_risk.json  — on risk_score = HIGH
```

**AWS S3 instead of MinIO:**
```env
STORAGE_ENDPOINT=           # leave blank — boto3 defaults to AWS
STORAGE_ACCESS_KEY=AKIA...
STORAGE_SECRET_KEY=...
STORAGE_BUCKET=your-production-bucket
```

**Sentry:**
```env
SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/789
```

### Disabling a Module

```bash
# API-only mode (no background workers)
docker compose up api db redis minio

# No frontend
docker compose up api worker db redis minio

# No n8n
docker compose up api worker db redis minio frontend

# Disable liveness at runtime
LIVENESS_ENABLED=false
```

---

## Principal Architect Setup Guide

### Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Docker | 24.0 | Required for containerised deployment |
| Docker Compose | 2.20 | Bundled with Docker Desktop |
| Python | 3.11 | Local development only |
| Node.js | 18 | Frontend local development only |
| UIDAI Public Key | RSA-2048 PEM | Obtain from uidai.gov.in — place at `certs/uidai_auth.pem` |

---

### Step 1 — Clone and Configure

```bash
git clone https://github.com/Tashima-Tarsh/aadhaar-verification-engine.git
cd aadhaar-verification-engine
cp .env.example .env
```

Open `.env` and fill in the required values (all others have working defaults for local dev):

```env
DATABASE_URL=postgresql+asyncpg://admin:password@db:5432/aadhaar_platform
REDIS_URL=redis://redis:6379/0
STORAGE_ENDPOINT=http://minio:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=aadhaar-platform
UIDAI_PUBLIC_KEY_PATH=certs/uidai_auth.pem
ENCRYPTION_KEY=<generate below>
JWT_SECRET=<generate below>
```

Generate secrets:
```bash
# ENCRYPTION_KEY (32-byte hex)
python3 -c "import secrets; print(secrets.token_hex(32))"

# JWT_SECRET
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

### Step 2 — Place the UIDAI Public Key

```bash
# Obtain the official UIDAI offline KYC public key PEM and place it at:
cp /path/to/uidai_offline_publickey.pem certs/uidai_auth.pem
```

> Without this file, QR signature validation (`qr_valid`) will return `null`. All other features — address extraction, risk scoring, photo extraction — continue to function.

---

### Step 3 — Start the Full Stack

```bash
docker compose up -d

# Monitor startup
docker compose logs -f api worker
```

Services:

| Service | URL | Default Credentials |
|---|---|---|
| REST API | http://localhost:8000 | — |
| Swagger UI | http://localhost:8000/api/docs | — |
| Frontend Dashboard | http://localhost:3000 | — |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| n8n Automation | http://localhost:5678 | admin / n8npassword |

---

### Step 4 — Apply Database Migrations

```bash
docker compose exec api alembic upgrade head
```

---

### Step 5 — Create Your First Tenant

```bash
curl -s -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyOrg",
    "webhook_url": "https://your-crm.com/aadhaar/callback",
    "webhook_secret": "your-hmac-secret"
  }' | python3 -m json.tool
```

Response:
```json
{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "MyOrg",
  "api_key": "plain-text-key-shown-once-save-it-now",
  "is_active": true
}
```

> The `api_key` is shown **once only**. Store it in your secret manager immediately.

---

### Step 6 — Verify a Single Document

```bash
curl -s -X POST http://localhost:8000/api/v1/verify \
  -H "X-API-Key: <your-api-key>" \
  -F "file=@/path/to/aadhaar.jpg" \
  -F "reference_id=TXN-2024-001" \
  | python3 -m json.tool
```

Poll for the result:
```bash
curl -s http://localhost:8000/api/v1/verify/<request_id>/status \
  -H "X-API-Key: <your-api-key>"
```

Full result (once COMPLETED):
```bash
curl -s http://localhost:8000/api/v1/verify/<request_id>/result \
  -H "X-API-Key: <your-api-key>"
```

---

### Step 7 — Bulk Processing

Submit up to 500 documents in a single API call:

```bash
curl -s -X POST http://localhost:8000/api/v1/batch \
  -H "X-API-Key: <your-api-key>" \
  -F "files=@aadhaar1.jpg" \
  -F "files=@aadhaar2.pdf" \
  -F "files=@aadhaar3.xml" \
  | python3 -m json.tool
```

Monitor the job:
```bash
curl -s http://localhost:8000/api/v1/batch/<job_id>/status \
  -H "X-API-Key: <your-api-key>"
```

Paginated results:
```bash
curl -s "http://localhost:8000/api/v1/batch/<job_id>/results?page=1&page_size=50" \
  -H "X-API-Key: <your-api-key>"
```

Scale workers for higher throughput:
```bash
docker compose up -d --scale worker=4
```

---

### Step 8 — CRM Direct Upload (Presigned S3)

For large files — bypass the API and upload directly to object storage:

```bash
# Step 1: Get a presigned upload URL
curl -s "http://localhost:8000/api/v1/storage/upload-url?file_name=aadhaar.pdf" \
  -H "X-API-Key: <your-api-key>"

# Step 2: PUT the file directly to the returned URL (no auth needed)
curl -s -X PUT "<upload_url>" \
  -H "Content-Type: application/pdf" \
  --data-binary @aadhaar.pdf

# Step 3: Submit verification using the returned object_key
curl -s -X POST http://localhost:8000/api/v1/verify \
  -H "X-API-Key: <your-api-key>" \
  -F "reference_id=TXN-001" \
  -F "storage_key=<object_key_from_step_1>"
```

---

### Step 9 — Reports and Export

```bash
# Summary statistics (last 30 days)
curl -s "http://localhost:8000/api/v1/reports/summary?days=30" \
  -H "X-API-Key: <your-api-key>"

# CSV export for compliance / reconciliation
curl -OJ "http://localhost:8000/api/v1/reports/export/csv?days=30" \
  -H "X-API-Key: <your-api-key>"
```

---

### Step 10 — Health Monitoring

```bash
# Liveness (used by load balancer)
curl http://localhost:8000/health

# Readiness (checks DB + Redis connectivity)
curl http://localhost:8000/health/ready
```

---

## Production Deployment Checklist

```
Infrastructure
□ UIDAI public key PEM placed at certs/uidai_auth.pem
□ DATABASE_URL points to managed PostgreSQL (AWS RDS / GCP Cloud SQL)
□ REDIS_URL points to managed Redis (AWS ElastiCache / Upstash)
□ STORAGE_ENDPOINT points to AWS S3 or equivalent (not local MinIO)
□ Worker replicas scaled to meet throughput SLA (docker compose --scale worker=N)

Security
□ ENCRYPTION_KEY is a securely generated 32-byte random hex string
□ JWT_SECRET is at least 48 characters of cryptographic random entropy
□ .env file is excluded from version control (.gitignore enforced)
□ API keys stored in secret manager (AWS Secrets Manager / HashiCorp Vault)
□ Webhook HMAC secrets set per tenant and rotated periodically

Operations
□ Alembic migrations applied: alembic upgrade head
□ First tenant created and API key delivered securely to client
□ Health endpoints monitored by load balancer or uptime service
□ SENTRY_DSN configured for error tracking and alerting
□ Log aggregation configured (CloudWatch / Datadog / ELK)
□ n8n workflows imported and activation verified (if using automation)
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/tenants` | Open | Register a new tenant (returns API key once) |
| POST | `/api/v1/auth/token` | Open | Obtain JWT access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Open | Rotate JWT tokens |
| POST | `/api/v1/verify` | Key / JWT | Submit single document — async |
| GET | `/api/v1/verify/{id}/status` | Key / JWT | Poll verification status |
| GET | `/api/v1/verify/{id}/result` | Key / JWT | Retrieve full result (COMPLETED only) |
| POST | `/api/v1/batch` | Key / JWT | Submit up to 500 documents |
| GET | `/api/v1/batch/{id}/status` | Key / JWT | Batch job progress |
| GET | `/api/v1/batch/{id}/results` | Key / JWT | Paginated batch results |
| POST | `/api/v1/storage/upload-url` | Key / JWT | Presigned S3 upload URL |
| GET | `/api/v1/storage/download-url` | Key / JWT | Presigned S3 download URL |
| GET | `/api/v1/reports/summary` | Key / JWT | Aggregated verification stats |
| GET | `/api/v1/reports/export/csv` | Key / JWT | CSV export for compliance |
| GET | `/health` | Open | Service liveness probe |
| GET | `/health/ready` | Open | DB + Redis readiness probe |
| GET | `/api/docs` | Open | Interactive Swagger UI |

---

## Supported Document Formats

| Format | Specification |
|---|---|
| JPEG / PNG / TIFF | Aadhaar card photograph — any orientation, any quality level |
| PDF | Password-protected eAadhaar PDF (password = DOB DDMMYYYY) |
| XML | eAadhaar XML — plain or AES-256 ZIP-protected |
| Secure QR V1 | Plain UTF-8 XML payload embedded in QR |
| Secure QR V2 | Binary zlib-compressed payload with RSA-SHA256 UIDAI signature |

---

## Documentation Index

| Document | Contents |
|---|---|
| [docs/SYSTEM_EXPLANATION.md](docs/SYSTEM_EXPLANATION.md) | Deep-dive into how verification, QR parsing, and risk scoring work |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | Full schema with field definitions and relationships |
| [docs/CRM_INTEGRATION_GUIDE.md](docs/CRM_INTEGRATION_GUIDE.md) | Step-by-step CRM integration with webhook examples |
| [docs/N8N_WORKFLOWS.md](docs/N8N_WORKFLOWS.md) | n8n automation workflow configuration |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Complete directory layout and module responsibilities |
| [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) | Testing approach, coverage targets, and test data |
| [docs/AUDIT_REPORT.md](docs/AUDIT_REPORT.md) | Security and compliance audit findings |
| [docs/tdd_idd.md](docs/tdd_idd.md) | Technical and Interface Design Document |

---

**CONFIDENTIAL — LICENSED ENTERPRISE USE ONLY**
© 2026 Platform Engineering — FinTech Division
