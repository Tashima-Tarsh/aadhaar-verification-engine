"""
WebhookService — fixed: hmac.new → hmac.new() with json.dumps payload encoding.
Added: exponential retry up to WEBHOOK_RETRY_COUNT.
"""
import hmac
import hashlib
import json
import asyncio
import httpx
import logging
from typing import Dict, Any, Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


class WebhookService:

    @staticmethod
    async def dispatch(
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
        max_retries: int = None,
    ) -> bool:
        max_retries = max_retries if max_retries is not None else settings.WEBHOOK_RETRY_COUNT
        body = json.dumps(payload, default=str)
        headers = {"Content-Type": "application/json"}

        if secret:
            sig = hmac.new(
                secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={sig}"

        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, content=body, headers=headers)
                    response.raise_for_status()
                    logger.info(f"Webhook delivered: {url} (attempt {attempt + 1})")
                    return True
            except httpx.HTTPStatusError as e:
                logger.warning(f"Webhook HTTP error {e.response.status_code} → {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"Webhook error: {e} → {url} (attempt {attempt + 1})")

            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s

        logger.error(f"Webhook failed after {max_retries + 1} attempts: {url}")
        return False
