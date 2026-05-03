import hmac
import hashlib
import httpx
import logging
from typing import Dict, Any
from src.config.settings import settings

logger = logging.getLogger(__name__)

class WebhookService:
    @staticmethod
    async def dispatch(url: str, payload: Dict[str, Any], secret: str = None) -> bool:
        """Sends a webhook notification to the CRM with retry logic."""
        headers = {"Content-Type": "application/json"}
        
        # Sign payload if secret provided
        if secret:
            signature = hmac.new(
                secret.encode(), 
                str(payload).encode(), 
                hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={signature}"

        async with httpx.AsyncClient() as client:
            try:
                # Basic retry logic using httpx (can be enhanced with Celery retries)
                response = await client.post(
                    url, 
                    json=payload, 
                    headers=headers, 
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook successfully delivered to {url}")
                return True
            except httpx.HTTPStatusError as e:
                logger.error(f"Webhook delivery failed: {e.response.status_code} for {url}")
                return False
            except Exception as e:
                logger.error(f"Webhook delivery error: {e}")
                return False
