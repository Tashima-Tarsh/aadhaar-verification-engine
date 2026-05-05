# GitHub Codespaces — Quick Start

## Open in Codespaces

Click the button below to launch a fully configured cloud environment.
No installation. No Docker setup. No configuration needed.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Tashima-Tarsh/aadhaar-verification-engine)

---

## What Happens Automatically

When the Codespace opens:

1. Ubuntu 22.04 environment is created
2. Docker and Python 3.11 are installed
3. `.env` file is generated with secure keys
4. UIDAI certificate is verified
5. Docker images are pre-pulled
6. All services start: API, DB, Redis, Workers, Dashboard, n8n

**Total time: 3–5 minutes. You do nothing.**

---

## Your URLs Inside Codespaces

| Service | Port | How to Open |
|---|---|---|
| Operator Dashboard | 3000 | Opens automatically in browser |
| API + Swagger Docs | 8000 | Ports tab → globe icon |
| MinIO Storage | 9001 | Ports tab → globe icon |
| n8n Automation | 5678 | Ports tab → globe icon |

---

## First Thing to Do

Once the dashboard opens at port 3000:

1. Go to **Upload** tab
2. Upload an Aadhaar image (JPG or PDF)
3. See results: name, DOB, address, risk score

Or create an API tenant and test via curl:

```bash
# Create tenant
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "MyCompany"}'

# Save the api_key from the response, then verify:
curl -X POST http://localhost:8000/api/v1/verify \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@aadhaar.jpg" \
  -F "reference_id=TEST-001"
```

---

## Stopping and Restarting Services

```bash
# Stop all
docker compose down

# Start all
docker compose up -d

# View logs
docker compose logs -f api
docker compose logs -f worker
```

---

## Scale to 5,000+ Verifications Per Day

```bash
docker compose up -d --scale worker=4
```

4 workers × 8 concurrent slots = handles 100,000+ verifications/day.
