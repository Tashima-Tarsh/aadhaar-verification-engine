# Aadhaar Offline Verification, Risk & Identity Intelligence Platform

## 🌟 Project Overview
The **Aadhaar Offline Verification Platform** is an enterprise-grade solution designed for secure, high-speed, and compliant identity verification. It enables organizations to verify Aadhaar identities without making online calls to UIDAI servers, adhering to the highest standards of data privacy and regulatory compliance.

The platform is built to handle degraded document inputs (B/W, blurred, rotated), extract rich demographic data, and provide real-time risk intelligence through a proprietary scoring engine.

---

## ✨ Features
- **100% Offline Compliance**: No outbound connections to UIDAI; verification is performed locally using RSA-SHA256 digital signature validation.
- **Multi-Format Ingestion**: Processes JPG, PNG, TIFF, password-protected PDFs, and encrypted eAadhaar XML/ZIP files.
- **Intelligent Preprocessing**: Advanced image transformation pipeline (Grayscale, CLAHE, Denoising, Deskew) to maximize QR success rates.
- **Risk Intelligence Engine**: Real-time scoring (LOW/MEDIUM/HIGH) based on signal quality, address completeness, and liveness.
- **Bulk Processing Pipeline**: Async queue-based processing for high-volume loads (5,000+ daily baseline).
- **Audit & Governance**: Immutable audit logs for every request with automated data retention policies.
- **Modern Dashboard**: High-performance, glassmorphism-based UI for real-time monitoring.

---

## 🏗️ Architecture Summary
The platform follows **Clean Architecture** principles and a layered service-oriented design:
- **API Gateway**: FastAPI for request ingestion, authentication (JWT + API Keys), and rate limiting.
- **Orchestration Layer**: Coordinates the verification flow between various specialized engines.
- **Verification Engine**: Multi-attempt QR cascade, UIDAI signature validation, and document parsing.
- **Async Layer**: Celery workers powered by Redis for reliable background processing and DLQ (Dead Letter Queue) support.
- **Data Persistence**: PostgreSQL for immutable records and Redis for ephemeral caching/queueing.

---

## 🛠️ Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy (Async), Pydantic v2
- **Image Processing**: OpenCV, Pillow, scikit-image, zxing-cpp
- **Security**: Cryptography (RSA), PyJWT, Fernet (Field-level encryption)
- **Infrastructure**: Docker, Docker Compose, Redis, PostgreSQL
- **Monitoring**: Prometheus, Grafana, Flower

---

## ⚙️ Environment Variables
Create a `.env` file in the root directory. See `.env.example` for details.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL Async Connection String | - |
| `REDIS_URL` | Redis Connection String | - |
| `STORAGE_ENDPOINT` | S3/MinIO Endpoint | - |
| `UIDAI_PUBLIC_KEY_PATH` | Path to UIDAI RSA Public Key | `certs/uidai_auth.pem` |
| `ENCRYPTION_KEY` | 32-byte hex key for Fernet | - |
| `JWT_SECRET` | Secret for JWT Token Generation | - |

---

## 🚀 Setup & Run Instructions

### Docker (Recommended)
The fastest way to spin up the entire production stack including DB, Cache, and Workers.

```bash
# 1. Build and start all services
docker-compose up --build -d

# 2. Access the Dashboard
# URL: http://localhost:8000/dashboard

# 3. Access API Documentation
# URL: http://localhost:8000/docs
```

### Local Development
Ensure you have Python 3.11+ and the required system libraries (libzbar0, libgl1).

```bash
# 1. Install dependencies
pip install .

# 2. Setup Environment
cp .env.example .env

# 3. Run the Application
python -m src.main
```

---

## 📄 Documentation
- **TDD/IDD**: [docs/tdd_idd.md](docs/tdd_idd.md)
- **Architecture Diagram**: [docs/architecture_diagram.png](docs/architecture_diagram.png)

---
**CONFIDENTIAL — INTERNAL ONLY**  
© 2026 Platform Engineering — FinTech Division
