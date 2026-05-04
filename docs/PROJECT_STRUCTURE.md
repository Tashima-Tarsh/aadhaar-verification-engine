# Project Structure — Aadhaar Offline Verification Platform

Complete directory layout of the platform covering backend engines, API layer, async workers, frontend dashboard, and infrastructure.

---

```text
aadhaar-verification-engine/
│
├── src/                                  # Backend — Python 3.11 / FastAPI
│   │
│   ├── main.py                           # FastAPI application entry point
│   │                                     # Registers all routers, CORS, middleware
│   │
│   ├── config/
│   │   └── settings.py                   # Pydantic BaseSettings — all env vars,
│   │                                     # validated at startup, no runtime surprises
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── routes/
│   │       │   ├── auth.py               # POST /auth/token (login)
│   │       │   │                         # POST /auth/refresh (rotate JWT)
│   │       │   │                         # POST /tenants (register)
│   │       │   │                         # POST /tenants/{id}/regenerate-key
│   │       │   │
│   │       │   ├── verify.py             # POST /verify (single document)
│   │       │   │                         # GET  /verify/{id}/status
│   │       │   │                         # GET  /verify/{id}/result
│   │       │   │
│   │       │   ├── batch.py              # POST /batch (up to 500 files)
│   │       │   │                         # GET  /batch/{id}/status
│   │       │   │                         # GET  /batch/{id}/results (paginated)
│   │       │   │
│   │       │   ├── reports.py            # GET  /reports/summary
│   │       │   │                         # GET  /reports/export/csv
│   │       │   │
│   │       │   ├── storage.py            # POST /storage/upload-url (presigned S3)
│   │       │   │                         # GET  /storage/download-url
│   │       │   │
│   │       │   └── health.py             # GET  /health (liveness)
│   │       │                             # GET  /health/ready (DB + Redis)
│   │       │
│   │       ├── dependencies/
│   │       │   └── auth.py               # get_current_tenant() — resolves tenant
│   │       │                             # from X-API-Key header or Bearer JWT
│   │       │
│   │       └── schemas/
│   │           └── verify.py             # All Pydantic request / response models:
│   │                                     # VerifyResponseSchema, BulkStatusSchema,
│   │                                     # TokenSchema, TenantResponseSchema,
│   │                                     # ReportSummarySchema, AddressSchema
│   │
│   ├── core/                             # Domain logic — framework-independent
│   │   ├── orchestrator.py               # 7-stage pipeline coordinator:
│   │   │                                 # preprocess → decode → validate signature
│   │   │                                 # → extract data → score risk → liveness
│   │   │                                 # → store result
│   │   │
│   │   ├── risk_scorer.py                # 6-signal weighted risk model
│   │   │                                 # Signals: QR validity (35pt), image
│   │   │                                 # quality (20pt), address completeness
│   │   │                                 # (15pt), photo (10pt), data completeness
│   │   │                                 # (10pt), liveness (10pt)
│   │   │                                 # Output: LOW / MEDIUM / HIGH + numeric
│   │   │
│   │   ├── liveness.py                   # PLUG-IN: DeepFace face verification
│   │   │                                 # Haar cascade fallback if GPU unavailable
│   │   │                                 # Controlled by LIVENESS_ENABLED env var
│   │   │
│   │   ├── database.py                   # SQLAlchemy async engine + session factory
│   │   │                                 # get_db() FastAPI dependency
│   │   │
│   │   ├── security.py                   # JWT create/decode, API key generation,
│   │   │                                 # password hashing (bcrypt), hash_api_key()
│   │   │
│   │   └── logging.py                    # structlog + Sentry initialisation
│   │
│   ├── engines/                          # Specialised processing engines
│   │   ├── preprocessing.py              # Fluent image builder:
│   │   │                                 # CLAHE contrast → deskew → Gaussian blur
│   │   │                                 # → denoising → UnsharpMask → adaptive
│   │   │                                 # threshold → morphological cleanup
│   │   │                                 # assess_quality() → float 0.0–1.0
│   │   │
│   │   ├── qr_decoder.py                 # Multi-engine QR cascade:
│   │   │                                 # 1. pyzbar (fastest)
│   │   │                                 # 2. zxing-cpp TryHarder mode
│   │   │                                 # 3. Inverted image variants
│   │   │                                 # 4. 4 cardinal rotations
│   │   │                                 # 5. Multi-scale (0.5×–2.0×)
│   │   │                                 # 6. QReader ML (deepest fallback)
│   │   │
│   │   ├── aadhaar_verifier.py           # QR V1 / V2 auto-detection and parsing
│   │   │                                 # Extracts: name, DOB, gender, UID,
│   │   │                                 # address, photo (base64)
│   │   │
│   │   ├── signature_validator.py        # UIDAI RSA-SHA256 offline validation
│   │   │                                 # Loads public key from UIDAI_PUBLIC_KEY_PATH
│   │   │
│   │   ├── document_processor.py         # PDF: pikepdf decrypt → PyMuPDF QR scan
│   │   │                                 # XML: pyzipper AES-256 → lxml XXE-safe
│   │   │
│   │   └── address_normalizer.py         # 29 Indian states + abbreviation map
│   │                                     # clean_placeholder(), normalize_full()
│   │                                     # Returns NormalizedAddress dataclass
│   │
│   ├── db/
│   │   ├── models.py                     # SQLAlchemy ORM models:
│   │   │                                 # Tenant, BulkJob, VerificationRequest,
│   │   │                                 # VerificationResult, AuditLog
│   │   │
│   │   └── repositories/
│   │       └── verification_repo.py      # Repository pattern — all DB queries
│   │                                     # create_request, get_request_by_id,
│   │                                     # get_request_by_reference, save_result,
│   │                                     # create_audit_log, update_request_status
│   │
│   ├── services/
│   │   ├── verification_service.py       # Single verification orchestrator:
│   │   │                                 # idempotency check → create record →
│   │   │                                 # run pipeline → save result → webhook
│   │   │
│   │   └── webhook_service.py            # HMAC-SHA256 signed HTTP POST to tenant URL
│   │                                     # Exponential retry (up to WEBHOOK_RETRY_COUNT)
│   │                                     # Header: X-Hub-Signature-256
│   │
│   ├── utils/
│   │   ├── crypto.py                     # AuthHandler (JWT encode/decode)
│   │   │                                 # encrypt_value() / decrypt_value() — Fernet
│   │   │
│   │   └── storage.py                    # StorageManager (boto3 S3 / MinIO)
│   │                                     # upload(), download(), save_upload()
│   │                                     # generate_presigned_upload_url()
│   │                                     # generate_presigned_download_url()
│   │
│   └── workers/
│       ├── celery_app.py                 # Celery config: Redis broker + backend
│       │                                 # Queues: aadhaar_verification, aadhaar_dlq
│       │                                 # DLQ policy: max_retries=3, acks_late=True
│       │
│       └── tasks.py                      # process_verification_task — downloads file
│                                         # from storage, runs service, retries with
│                                         # exponential backoff (2s → 4s → 8s)
│                                         # dead_letter_handler — DLQ permanent failure
│                                         # K8s heartbeat: writes /tmp/worker_healthy
│                                         # every 15s (probe checks mtime < 45s)
│
├── frontend/                             # Operator dashboard — Next.js 14
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                # Root layout with sticky navigation bar
│   │   │   ├── dashboard/page.tsx        # Summary stats overview
│   │   │   ├── upload/page.tsx           # Single document verify + live polling
│   │   │   ├── batch/page.tsx            # Multi-file dropzone + progress bar
│   │   │   ├── results/page.tsx          # Request ID lookup + full result card
│   │   │   └── reports/page.tsx          # Risk pie chart + CSV export
│   │   │
│   │   └── lib/
│   │       └── api.ts                    # Axios client with JWT auto-refresh
│   │                                     # interceptor — attaches API key or Bearer
│   │
│   ├── package.json                      # Dependencies: next, react, recharts,
│   │                                     # react-dropzone, tanstack/react-query, axios
│   ├── next.config.js                    # API proxy rewrite → backend
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── docker/
│   ├── app.Dockerfile                    # API container (multi-stage, slim runtime)
│   ├── worker.Dockerfile                 # Worker container with K8s HEALTHCHECK
│   │                                     # CMD: checks /tmp/worker_healthy mtime
│   └── frontend.Dockerfile              # Next.js standalone output container
│
├── n8n/
│   └── workflows/
│       ├── workflow_success.json         # Trigger: status == COMPLETED
│       ├── workflow_failure.json         # Trigger: status == FAILED
│       └── workflow_high_risk.json       # Trigger: risk_score == HIGH (escalation)
│
├── certs/
│   └── uidai_auth.pem                    # UIDAI RSA-2048 public key (not committed)
│   └── uidai_auth.pem.example            # Placeholder showing expected format
│
├── docs/                                 # Technical documentation
│   ├── SYSTEM_EXPLANATION.md
│   ├── DATABASE_SCHEMA.md
│   ├── CRM_INTEGRATION_GUIDE.md
│   ├── N8N_WORKFLOWS.md
│   ├── PROJECT_STRUCTURE.md              # This file
│   ├── TESTING_STRATEGY.md
│   ├── AUDIT_REPORT.md
│   ├── tdd_idd.md
│   └── architecture_diagram.png
│
├── tests/
│   └── unit/                             # Pytest unit tests (pytest-asyncio)
│
├── pyproject.toml                        # All dependencies + optional extras:
│                                         # pip install .           → core
│                                         # pip install ".[liveness]" → + DeepFace
│                                         # pip install ".[test]"   → + test tools
│
├── docker-compose.yml                    # Full local stack:
│                                         # db, redis, minio, api, worker,
│                                         # worker_dlq, frontend, n8n
│                                         # All services include healthchecks
│
├── .env.example                          # All supported env vars with descriptions
├── .gitignore                            # Python, Node, secrets, certs excluded
└── README.md                             # Platform landing page
```

---

## Design Principles

**1. Plug-In / Plug-Out Modules**
Every component beyond the core engine is independently toggleable via environment variables or compose service inclusion. No code changes required to enable or disable liveness, webhooks, n8n, or the frontend.

**2. Separation of Concerns**
Core domain logic (`src/core/`, `src/engines/`) has zero dependency on FastAPI or HTTP. It can be invoked from a Celery task, a CLI script, or a test without starting the server.

**3. Repository Pattern**
All database access is channelled through `VerificationRepository`. Business logic never writes SQL directly — enabling full mock substitution in tests.

**4. Environment-First Configuration**
Every configurable behaviour is driven by environment variables validated at startup by Pydantic Settings. The application refuses to start with invalid configuration rather than failing silently at runtime.

**5. Async-Native**
FastAPI, SQLAlchemy, and all I/O operations use Python's async/await throughout. No thread-blocking calls in the hot path.

**6. Defence in Depth**
- API keys stored as SHA-256 hashes only (never plaintext)
- Document passwords encrypted with Fernet before storage
- Webhook payloads signed with HMAC-SHA256
- XML parsing configured with `resolve_entities=False, no_network=True` (XXE protection)
- Presigned URLs scope downloads to the requesting tenant's prefix
