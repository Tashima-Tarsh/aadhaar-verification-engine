# Project Structure — Aadhaar Offline Verification Platform

This document outlines the complete directory layout for the enterprise implementation, covering the backend, frontend, and infrastructure layers.

```text
aadhaar-verification-platform/
├── src/                        # Backend Source (Python/FastAPI)
│   ├── api/                    # API Layer
│   │   ├── v1/                 # Version 1 API
│   │   │   ├── routes/         # Endpoint handlers (verify.py, bulk.py)
│   │   │   └── schemas/        # Pydantic request/response models
│   │   └── middleware/         # Auth, Logging, Rate Limiting
│   ├── core/                   # Core Domain Logic (Framework Independent)
│   │   ├── orchestrator.py     # Main verification workflow
│   │   ├── risk_scorer.py      # Weighted risk scoring engine
│   │   └── liveness.py         # Face detection & feature matching
│   ├── engines/                # Specialized Processing Engines
│   │   ├── preprocessing.py    # Image enhancement pipeline
│   │   ├── qr_decoder.py       # Multi-library QR cascade
│   │   ├── signature_validator.py # UIDAI RSA validation
│   │   ├── document_processor.py  # PDF/XML/ZIP parsing
│   │   ├── photo_extractor.py  # Normalized photo extraction
│   │   └── address_normalizer.py # Address cleaning rules
│   ├── workers/                # Async Worker Layer
│   │   ├── tasks.py            # Celery task definitions
│   │   └── celery_app.py       # Celery configuration
│   ├── db/                     # Data Persistence Layer
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── repositories/       # Repository Pattern implementations
│   │   └── migrations/         # Alembic database migrations
│   ├── services/               # Application Services
│   │   ├── verification_service.py # Orchestrates single verification
│   │   ├── bulk_service.py     # Manages bulk job lifecycles
│   │   └── webhook_service.py  # Dispatcher for CRM callbacks
│   ├── config/                 # Configuration Management
│   │   └── settings.py         # Pydantic BaseSettings (Env-based)
│   ├── utils/                  # Shared Utilities (Crypto, Files)
│   └── main.py                 # FastAPI Application Entrypoint
│
├── frontend/                   # Frontend Dashboard (Next.js/React)
│   ├── app/                    # Next.js App Router
│   ├── components/             # Reusable UI Components
│   ├── services/               # API Client services
│   └── public/                 # Static assets
│
├── infra/                      # Infrastructure & DevOps
│   ├── docker/                 # Dockerfiles (app, worker, frontend)
│   ├── terraform/              # IaC (Optional)
│   ├── prometheus/             # Monitoring config
│   └── grafana/                # Dashboard templates
│
├── tests/                      # Automated Test Suite
│   ├── unit/                   # Isolated logic tests
│   ├── integration/            # DB and I/O tests
│   └── e2e/                    # Full API flow tests
│
├── certs/                      # Security Certificates (UIDAI PEM)
├── docs/                       # Technical Documentation & Diagrams
├── pyproject.toml              # Python dependencies & build config
├── docker-compose.yml          # Local development stack
├── .env.example                # Template for environment variables
└── README.md                   # Project landing page
```

---

## Key Organization Principles
1. **Separation of Concerns**: Core business logic (`src/core`) is isolated from the framework (`src/api`).
2. **Engines Pattern**: Every specialized task (QR, PDF, Risk) has its own modular engine.
3. **Repository Pattern**: Database access is abstracted to enable easy mocking and DB swapping.
4. **Environment First**: All configuration is driven by environment variables via Pydantic.
