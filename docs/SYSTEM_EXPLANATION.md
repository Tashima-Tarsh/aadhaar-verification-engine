# System Explanation — Aadhaar Offline Verification Platform

This document provides a deep dive into the internal mechanics of the platform, explaining how various components interact to provide secure and compliant identity verification.

---

## 1. What the System Does
The platform acts as a high-performance intermediary between identity documents and enterprise systems (like CRMs). It ingests raw document files, validates their authenticity using cryptographic signatures, extracts demographic and biometric (photo) data, and performs a risk assessment to determine the validity of the identity claim.

---

## 2. How Aadhaar Offline Verification Works
Unlike "Online Aadhaar" (eKYC) which requires an OTP and a direct call to UIDAI, **Offline Verification** utilizes the **Secure QR Code** or **eAadhaar XML** provided by UIDAI.
- **Digital Trust**: Every Secure QR code is digitally signed by UIDAI using an RSA-2048 private key.
- **Local Validation**: Our system stores the UIDAI Public Key. When a QR is scanned, we use this key to verify the RSA-SHA256 signature. If the signature matches the data, the document is proven to be authentic and untampered, without ever needing an internet connection.

---

## 3. QR + XML/PDF Processing
The system uses a multi-engine ingestion pipeline:
- **QR Decoding**: Uses a cascade of libraries (OpenCV -> pyzbar -> zxing-cpp) to detect and decode the QR. If the image is blurry, the "Image Preprocessing Pipeline" sharpens it; if it's dark, it normalizes brightness.
- **PDF Processing**: Decrypts password-protected PDFs (usually the user's DOB) and uses OCR/Text extraction along with QR image extraction.
- **XML/ZIP Processing**: Parses eAadhaar XML files. If the file is a password-protected ZIP, it uses the provided PIN to decrypt the internal XML.

---

## 4. How Risk Scoring Works
Risk scoring is not binary; it's a composite score (0-100) calculated from multiple "Signals":
- **QR Validity (35 pts)**: Is the signature authentic?
- **Image Quality (20 pts)**: Is the document clear enough to prevent impersonation?
- **Address Completeness (15 pts)**: Are all critical fields (PIN, State, District) present?
- **Photo Status (10 pts)**: Is a valid face image extractable?
- **Liveness (20 pts)**: Does the selfie match the document?

**Classifications**:
- **LOW (0-20)**: High confidence, straight-through processing.
- **MEDIUM (21-45)**: Slight discrepancies, manual review suggested.
- **HIGH (46-100)**: Potential fraud or corrupted data, immediate investigation required.

---

## 5. How Liveness Works
The Liveness module (Optional) uses a two-step process:
1. **Face Detection**: Uses MediaPipe/OpenCV to locate the face in both the Aadhaar document and a provided "selfie".
2. **Feature Matching**: Performs a facial embedding comparison to ensure the person holding the document is the same person on the document. (Note: Full liveness like blink detection requires video stream processing).

---

## 6. How Queue + Workers Work
To handle bulk loads (e.g., 5,000 requests at once), the system uses an **Asynchronous Task Pattern**:
1. **Producer**: The FastAPI API receives the files and pushes a "Job" into the Redis Queue.
2. **Broker**: Redis manages the queue of pending tasks.
3. **Consumer**: Celery Workers (horizontally scalable) pick up tasks as they become free, process the verification, and save results to the DB.
4. **DLQ (Dead Letter Queue)**: If a job fails multiple times, it's moved to a DLQ for manual inspection, preventing "poison pills" from blocking the queue.

---

## 7. How Webhook Works
For bulk jobs, the system doesn't require the client to wait. 
- Once a job (or a batch) is completed, the **Webhook Service** retrieves the client's `webhook_url`.
- It POSTS the full JSON result to that URL with a secure HMAC-SHA256 signature in the header.
- **Retry Logic**: If the client's server is down, the system uses an exponential backoff strategy to retry the delivery up to 5 times.
