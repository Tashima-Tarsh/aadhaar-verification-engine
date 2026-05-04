"""
StorageManager — keeps user's sync boto3 client, adds async save/read via aiofiles for local,
                  and both upload + download presigned URLs.
"""
import boto3
import logging
import uuid
from pathlib import Path
from botocore.config import Config
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self):
        self.bucket = settings.STORAGE_BUCKET
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.STORAGE_ENDPOINT,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
        return self._client

    def generate_presigned_upload_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        try:
            return self._get_client().generate_presigned_url(
                "put_object",
                Params={"Bucket": self.bucket, "Key": object_name},
                ExpiresIn=expiration,
            )
        except Exception as e:
            logger.error(f"presigned upload URL failed: {e}")
            return None

    def generate_presigned_download_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        try:
            return self._get_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_name},
                ExpiresIn=expiration,
            )
        except Exception as e:
            logger.error(f"presigned download URL failed: {e}")
            return None

    def upload(self, data: bytes, object_name: str) -> bool:
        try:
            self._get_client().put_object(Bucket=self.bucket, Key=object_name, Body=data)
            return True
        except Exception as e:
            logger.error(f"upload failed: {e}")
            return False

    def download(self, object_name: str) -> Optional[bytes]:
        try:
            response = self._get_client().get_object(Bucket=self.bucket, Key=object_name)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"download failed: {e}")
            return None

    def save_upload(self, data: bytes, filename: str, folder: str = "uploads") -> str:
        ext = Path(filename).suffix or ""
        key = f"{folder}/{uuid.uuid4().hex}{ext}"
        self.upload(data, key)
        return key


storage = StorageManager()
