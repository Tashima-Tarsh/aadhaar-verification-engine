# Installation & Setup Guide
## Aadhaar Offline Verification Platform

This guide takes you from zero to a fully running platform in under 30 minutes.
No cloud account. No UIDAI API key. No third-party dependency. Everything runs on your own server.

---

## What You Need Before Starting

| Requirement | Minimum Spec | Notes |
|---|---|---|
| Operating System | Windows 10 / Ubuntu 20.04 / macOS 12 | Any 64-bit OS |
| RAM | 8 GB | 16 GB recommended for 5,000/day |
| Disk | 20 GB free | For DB, images, logs |
| Docker Desktop | Latest | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| Git | Any version | [git-scm.com](https://git-scm.com) |
| Internet | Required first time only | To pull Docker images (~3 GB) |

---

## Step 1 — Install Docker Desktop

### Windows / Mac
1. Download from: https://www.docker.com/products/docker-desktop
2. Run the installer — accept all defaults
3. Start Docker Desktop from your applications menu
4. Wait until you see **Docker is running** in the system tray

### Ubuntu / Debian Linux
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

Verify Docker is working:
```bash
docker run hello-world
```
You should see: `Hello from Docker!`

---

## Step 2 — Download the Platform

```bash
git clone https://github.com/Tashima-Tarsh/aadhaar-verification-engine.git
cd aadhaar-verification-engine
```

---

## Step 3 — Generate Your Security Keys

Run this command — it prints two keys you will need in the next step:

```bash
python3 -c "
import secrets
print('ENCRYPTION_KEY=' + secrets.token_hex(32))
print('JWT_SECRET=' + secrets.token_urlsafe(48))
"
```

Save both values. You will paste them into the `.env` file below.

> If Python is not installed: download from https://python.org — only needed for this one command.

---

## Step 4 — Create Your Environment File

Copy the template:

```bash
cp .env.example .env
```

Open `.env` in any text editor (Notepad, nano, VS Code) and set these values:

```env
# Database — do not change these for Docker setup
DATABASE_URL=postgresql+asyncpg://admin:password@db:5432/aadhaar_platform
REDIS_URL=redis://redis:6379/0

# Storage — do not change for Docker setup
STORAGE_ENDPOINT=http://minio:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=aadhaar-platform

# UIDAI Certificate — already included in repo
UIDAI_PUBLIC_KEY_PATH=certs/uidai_offline_publickey_2026.cer

# Paste your generated keys here
ENCRYPTION_KEY=<paste ENCRYPTION_KEY value from Step 3>
JWT_SECRET=<paste JWT_SECRET value from Step 3>

# Leave these as-is
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
API_PREFIX=/api/v1
APP_VERSION=1.0.0
RATE_LIMIT_PER_MINUTE=100
MAX_BULK_UPLOAD_MB=500
MAX_BULK_FILES=500
WEBHOOK_RETRY_COUNT=3
LIVENESS_ENABLED=false
LOG_LEVEL=INFO
```

---

## Step 5 — Start the Platform

```bash
docker compose up --build
```

First time takes **5–10 minutes** (downloads and builds all containers).
Every time after that takes **30 seconds**.

You will know it is ready when you see all these lines:

```
aadhaar_db       | database system is ready to accept connections
aadhaar_redis    | Ready to accept connections
aadhaar_api      | Uvicorn running on http://0.0.0.0:8000
aadhaar_frontend | ready - started server on 0.0.0.0:3000
```

---

## Step 6 — Confirm All Services Are Healthy

Open a new terminal and run:

```bash
docker compose ps
```

Every service must show **Up** and **healthy**:

```
NAME                  STATUS          PORTS
aadhaar_db            Up (healthy)    0.0.0.0:5432->5432/tcp
aadhaar_redis         Up (healthy)    0.0.0.0:6379->6379/tcp
aadhaar_storage       Up (healthy)    0.0.0.0:9000->9000/tcp
aadhaar_api           Up (healthy)    0.0.0.0:8000->8000/tcp
aadhaar_worker        Up (healthy)
aadhaar_worker_dlq    Up
aadhaar_frontend      Up              0.0.0.0:3000->3000/tcp
aadhaar_n8n           Up              0.0.0.0:5678->5678/tcp
```

Run one final health check:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "version": "1.0.0"}
```

---

## Step 7 — Create Your First Tenant

A tenant is your organisation's account. This gives you an API key to authenticate all requests.

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "YourCompanyName"}'
```

Response:
```json
{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "YourCompanyName",
  "api_key": "64-character-hex-key-shown-only-once",
  "is_active": true
}
```

**Save the `api_key` immediately — it is shown only once and cannot be recovered.**

---

## Step 8 — Verify Your First Aadhaar

### Via the Dashboard (easiest)
Open your browser and go to:
```
http://localhost:3000
```
Click **Upload** → select an Aadhaar image (JPG, PNG, or PDF) → Submit.

### Via API (for CRM / system integration)

**Submit a document:**
```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "X-API-Key: YOUR_64_CHAR_API_KEY" \
  -F "file=@aadhaar_scan.jpg" \
  -F "reference_id=CUST-001"
```

Response:
```json
{
  "request_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "PENDING"
}
```

**Check the result (poll until COMPLETED):**
```bash
curl http://localhost:8000/api/v1/verify/{request_id}/status \
  -H "X-API-Key: YOUR_64_CHAR_API_KEY"
```

**Get full result with extracted data:**
```bash
curl http://localhost:8000/api/v1/verify/{request_id}/result \
  -H "X-API-Key: YOUR_64_CHAR_API_KEY"
```

Result includes:
```json
{
  "status": "COMPLETED",
  "qr_valid": true,
  "name": "Ramesh Kumar",
  "dob": "1990-05-15",
  "gender": "M",
  "masked_aadhaar": "XXXX-XXXX-3456",
  "address": {
    "house": "12", "street": "MG Road", "city": "Bangalore",
    "state": "Karnataka", "pincode": "560001"
  },
  "risk_score": "LOW",
  "processing_time_ms": 420
}
```

---

## Step 9 — Connect Your CRM

Point your CRM or internal system to these API endpoints:

| Operation | Method | URL |
|---|---|---|
| Submit document | POST | `http://localhost:8000/api/v1/verify` |
| Check status | GET | `http://localhost:8000/api/v1/verify/{id}/status` |
| Get full result | GET | `http://localhost:8000/api/v1/verify/{id}/result` |
| Submit bulk batch | POST | `http://localhost:8000/api/v1/batch` |
| Reports summary | GET | `http://localhost:8000/api/v1/reports/summary` |
| Export CSV | GET | `http://localhost:8000/api/v1/reports/export/csv` |

All requests require the header:
```
X-API-Key: YOUR_64_CHAR_API_KEY
```

Full interactive API documentation available at:
```
http://localhost:8000/api/docs
```

---

## Step 10 — Scale to 5,000 Verifications Per Day

The default setup handles 5,000 verifications/day out of the box.
If you need more throughput, add more worker processes:

```bash
docker compose up --scale worker=4
```

This runs 4 parallel workers. Each worker handles 8 concurrent tasks.
4 workers × 8 slots = **32 parallel verifications** = handles 100,000+/day.

No code change. No licence change. Just one command.

---

## Service URLs Reference

| Service | URL | Purpose |
|---|---|---|
| Operator Dashboard | http://localhost:3000 | Upload, view results, reports |
| API | http://localhost:8000 | REST API for CRM integration |
| API Documentation | http://localhost:8000/api/docs | Interactive Swagger UI |
| MinIO Storage Console | http://localhost:9001 | View uploaded documents |
| n8n Automation | http://localhost:5678 | Workflow triggers (user: admin / pass: n8npassword) |

---

## Stopping and Starting

**Stop all services (data preserved):**
```bash
docker compose down
```

**Start again:**
```bash
docker compose up
```

**Stop and delete all data (full reset):**
```bash
docker compose down -v
```

---

## Common Issues and Fixes

### Docker says "port already in use"
Another service is using port 8000 or 3000. Stop it or change the port in `docker-compose.yml`.

### `docker compose up` hangs at image pull
Check your internet connection. Run again — Docker resumes from where it stopped.

### API returns 401 Unauthorized
Your API key is wrong or expired. Create a new tenant via Step 7.

### Verification stays PENDING forever
The worker is not running. Check: `docker compose ps` — `aadhaar_worker` must show **Up**.

### `ERROR: Couldn't connect to Docker daemon`
Docker Desktop is not running. Open Docker Desktop from your applications and wait for it to show **Running**.

---

## Backup Your Data

All data lives in Docker volumes. Back up with:

```bash
# Backup database
docker exec aadhaar_db pg_dump -U admin aadhaar_platform > backup_$(date +%Y%m%d).sql

# Backup uploaded documents (MinIO)
docker cp aadhaar_storage:/data ./minio_backup_$(date +%Y%m%d)
```

---

## Support

For technical issues, refer to the API documentation at `http://localhost:8000/api/docs`.

For source code questions, see `docs/SYSTEM_EXPLANATION.md` and `docs/DATABASE_SCHEMA.md` in this repository.

---

---

## Why This Platform Is Unique

There is no other product in the Indian market that does what this platform does.

Every existing Aadhaar verification solution — Digio, IDfy, Karza, AuthBridge, Signzy — works the same way: your customer's data leaves your server, travels to their API, verification happens on their infrastructure, and you pay per call. You have no control over what happens to that data. You pay forever. And if their API goes down, your KYC goes down.

This platform breaks that model completely.

Verification happens entirely inside your own server. The Aadhaar QR code is decoded locally. The UIDAI digital signature is validated locally using the government-issued RSA public key that is included in this repository. Your customer's name, date of birth, Aadhaar number, and address never leave your network. Not even once.

The platform does not call UIDAI servers. It does not call any third-party API. It has no external dependency at runtime. If the internet goes down, verification still works. If UIDAI's servers go down, verification still works. If your API vendor raises prices, it does not matter — you have no API vendor.

On top of that, this is the only offline Aadhaar platform that combines six things no other product has together: a multi-engine QR cascade that handles degraded, blurred, and rotated documents; UIDAI RSA-SHA256 offline signature validation; a six-signal weighted risk intelligence engine that scores every document; a multi-tenant architecture for multiple business units; async bulk processing for up to 500 documents per batch; and a full operator dashboard — all in one deployable package.

UIDAI's own offline toolkit is a raw SDK. It has no pipeline, no risk scoring, no dashboard, no multi-tenancy, no queue, no retry logic, no audit log, no CRM integration. It is a library, not a product. This platform is the product layer that no one else has built.

You buy it once. You own it forever. You pay nothing per verification. Your data never leaves. And you can scale to 100,000 verifications per day by running one command.

That is what makes it unique. That is what makes it worth ₹50 lakhs.

---

*Platform version 1.0.0 — Built for the Indian fintech market — Validated against UIDAI offline public key (valid until February 2029)*
