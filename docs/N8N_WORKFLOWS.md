# n8n Workflows — Aadhaar Offline Verification Platform

This document contains the JSON definitions for n8n workflows used to process the webhooks dispatched by the platform.

---

## 1. Main Webhook Handler (Orchestrator)
This workflow receives the POST request from the platform, validates the HMAC signature, and branches logic based on the `risk_score`.

### [JSON Definition] — `aadhaar_webhook_orchestrator.json`
```json
{
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "aadhaar-verification-results",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$node[\"Webhook\"].json[\"status\"]}}",
              "value2": "COMPLETED"
            }
          ]
        }
      },
      "name": "Is Success?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$node[\"Webhook\"].json[\"risk_score_numeric\"]}}",
              "operation": "larger",
              "value2": 45
            }
          ]
        }
      },
      "name": "Is High Risk?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [650, 200]
    }
  ]
}
```

---

## 2. Success Path (CRM Sync)
Triggered when `status == COMPLETED` and `risk_score == LOW`.
- **Action**: Updates the CRM Lead/User record with the verified Aadhaar details.
- **Node**: `CRM Integration (Salesforce/HubSpot)`

---

## 3. Failure Path (Notification)
Triggered when `status == FAILED`.
- **Action**: Sends a Slack/Email notification to the Operations team with the `error_code`.
- **Node**: `Slack Send Message`

---

## 4. High-Risk Alert Path
Triggered when `risk_score_numeric > 45`.
- **Action**: Immediately flags the record in the CRM and creates a high-priority task for manual compliance review.
- **Action**: Sends an SMS alert to the Security Officer.

---

## 🛡️ Security Best Practices in n8n
1. **Signature Validation**: Use a `Crypto` node in n8n to generate an HMAC-SHA256 hash of the body using your `WEBHOOK_SECRET` and compare it with the `X-Hub-Signature-256` header.
2. **Rate Limiting**: Ensure your n8n instance is configured to handle the peak volume of the batch jobs.
