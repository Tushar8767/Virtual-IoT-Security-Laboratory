"""
Security Utilities

Provides:
- Password/credential hashing (bcrypt)
- JWT token creation and verification
- Device credential generation
- API key utilities

No hard-coded secrets. All secrets come from settings.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
import structlog
from jose import JWTError, jwt

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ============================================================
# Credential Hashing (using bcrypt directly)
# ============================================================

def hash_credential(plain: str) -> str:
    """Hash a plain-text credential using bcrypt."""
    # Truncate to 72 bytes (bcrypt limit) before encoding
    key_bytes = plain.encode("utf-8")[:72]
    salt = _bcrypt.gensalt(rounds=12)
    return _bcrypt.hashpw(key_bytes, salt).decode("utf-8")


def verify_credential(plain: str, hashed: str) -> bool:
    """Verify a plain-text credential against its bcrypt hash."""
    try:
        key_bytes = plain.encode("utf-8")[:72]
        return _bcrypt.checkpw(key_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


# ============================================================
# Device Credential Generation
# ============================================================

def generate_device_api_key() -> str:
    """
    Generate a cryptographically secure device API key.
    Format: iot-{random_hex_48}
    """
    return f"iot-{secrets.token_hex(24)}"


def generate_device_credential_pair() -> tuple[str, str]:
    """
    Generate a (plain_key, hashed_key) pair for a device.
    Only the hashed_key is stored. plain_key is returned once.
    """
    plain_key = generate_device_api_key()
    hashed_key = hash_credential(plain_key)
    return plain_key, hashed_key


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for tracing."""
    return str(uuid.uuid4())


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


# ============================================================
# JWT Tokens (for internal/user authentication if needed)
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    The subject (sub) claim should identify the entity.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    Returns the payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        return None


# ============================================================
# HMAC-based device token validation
# ============================================================

def create_device_token(device_id: str, secret: str) -> str:
    """
    Create an HMAC-SHA256 token for device identity.
    Used for lightweight device authentication.
    """
    message = f"{device_id}:{settings.DEVICE_PROVISIONING_SECRET}"
    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def safe_string_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.
    """
    return hmac.compare_digest(a.encode(), b.encode())
