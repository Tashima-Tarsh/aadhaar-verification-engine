import boto3
from botocore.config import Config
from src.config.settings import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.STORAGE_ENDPOINT,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1' # Default for MinIO
        )

    def generate_presigned_upload_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        """Generates a pre-signed URL to upload a file directly to S3/MinIO."""
        try:
            response = self.s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': settings.STORAGE_BUCKET, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            logger.error(f"Failed to generate pre-signed upload URL: {e}")
            return None

    def generate_presigned_download_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        """Generates a pre-signed URL to download a file."""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.STORAGE_BUCKET, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            logger.error(f"Failed to generate pre-signed download URL: {e}")
            return None
