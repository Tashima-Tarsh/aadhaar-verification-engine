from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class SignatureValidator:
    def __init__(self, public_key_path: str):
        self.public_key_path = public_key_path
        self._public_key = self._load_public_key()

    def _load_public_key(self):
        try:
            with open(self.public_key_path, "rb") as key_file:
                return serialization.load_pem_public_key(key_file.read())
        except Exception as e:
            logger.error(f"Failed to load UIDAI public key: {e}")
            raise

    def verify_signature(self, raw_bytes: bytes) -> Tuple[bool, Optional[bytes]]:
        """
        Validates the RSA-SHA256 signature of the Aadhaar Secure QR bytes.
        The last 256 bytes are the signature.
        """
        if len(raw_bytes) < 256:
            return False, None

        signature = raw_bytes[-256:]
        signed_data = raw_bytes[:-256]

        try:
            self._public_key.verify(
                signature,
                signed_data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True, signed_data
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False, None
