# CRM Integration Guide — Aadhaar Verification Platform

This guide provides technical specifications for integrating external CRM systems (e.g., Salesforce, HubSpot, or custom portals) with the Aadhaar Verification Platform.

---

## 1. Interaction Flow
The platform uses an **Asynchronous Storage-First** pattern to handle high-resolution identity documents without overloading the API server.

1. **URL Request**: CRM requests a pre-signed upload URL.
2. **Direct Upload**: CRM uploads the document directly to the Storage Service (S3/MinIO).
3. **Trigger**: CRM submits the verification request referencing the uploaded file key.
4. **Processing**: Platform processes the file in the background.
5. **Callback**: Platform notifies CRM via Webhook once verification is complete.

---

## 2. Step-by-Step Implementation

### Step 1: Request Pre-signed URL
**Endpoint**: `POST /api/v1/storage/upload-url`
```json
{
  "file_name": "aadhaar_front.jpg",
  "file_type": "image/jpeg"
}
```
**Response**:
```json
{
  "upload_url": "https://storage.yourdomain.com/uploads/...",
  "object_key": "uploads/f47ac10b-aadhaar_front.jpg"
}
```

### Step 2: Upload Document
The CRM must perform a standard HTTP `PUT` request to the `upload_url` provided.
```bash
curl -X PUT --upload-file ./aadhaar.jpg "https://storage.yourdomain.com/..."
```

### Step 3: Submit Verification Request
**Endpoint**: `POST /api/v1/verify`
```json
{
  "reference_id": "CRM_LEAD_9921",
  "storage_key": "uploads/f47ac10b-aadhaar_front.jpg",
  "source_type": "IMAGE"
}
```

---

## 3. Webhook Specification
Once processing is finished, the platform sends a `POST` request to your configured `webhook_url`.

### Payload Example (Success)
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "reference_id": "CRM_LEAD_9921",
  "status": "COMPLETED",
  "name": "SURESH KUMAR",
  "masked_aadhaar": "XXXX-XXXX-1234",
  "risk_score": "LOW",
  "risk_numeric": 12,
  "address": {
    "full": "123, MG Road, Bangalore, Karnataka, 560001",
    "pin": "560001"
  }
}
```

### Payload Example (High Risk)
```json
{
  "request_id": "...",
  "status": "COMPLETED",
  "risk_score": "HIGH",
  "risk_numeric": 85,
  "risk_flags": ["SIGNATURE_INVALID", "BLURRY_IMAGE"]
}
```

---

## 4. Security & Authentication
- **API Key**: All requests must include `X-API-Key` in the header.
- **Webhook Signing**: Verify the `X-Hub-Signature-256` header using your `WEBHOOK_SECRET` to ensure the callback originated from the platform.

---

## 5. Error Handling
| Code | Meaning | Action |
|------|---------|--------|
| `E001` | QR Detection Failed | Ask user to re-upload a clearer photo. |
| `E002` | Signature Invalid | Flag as high-risk/fraud attempt. |
| `E003` | Storage Key Expired | Generate a new upload URL. |

---

## 6. Best Practices
1. **Idempotency**: Use your internal Lead ID as the `reference_id` to prevent duplicate processing.
2. **Timeouts**: The background worker can take 2-10 seconds depending on load. Always use the Webhook flow rather than polling.
3. **Data Security**: Never store the raw, decrypted Aadhaar XML in your CRM unless compliant with UIDAI data vault policies. Use the platform's masking.
