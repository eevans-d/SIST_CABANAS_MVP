import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

import structlog
from app.core.config import get_settings
from fastapi import HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = structlog.get_logger()
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT tokens
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("jwt_verification_failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid token")


# WhatsApp signature verification
async def verify_whatsapp_signature(request: Request) -> bytes:
    """
    Verify WhatsApp webhook signature and return raw body.
    IMPORTANT: Only read body once!
    """
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not signature.startswith("sha256="):
        logger.warning("whatsapp_signature_invalid_format", signature=signature[:20])
        raise HTTPException(status_code=403, detail="Invalid signature format")

    # Read body only once
    body = await request.body()

    # Calculate expected signature
    expected = hmac.new(settings.WHATSAPP_APP_SECRET.encode(), body, hashlib.sha256).hexdigest()

    # Extract received signature (remove "sha256=" prefix)
    received = signature[7:]

    # Compare signatures
    if not hmac.compare_digest(expected, received):
        logger.warning("whatsapp_signature_mismatch")
        raise HTTPException(status_code=403, detail="Invalid signature")

    return body


# Mercado Pago signature verification
def verify_mercadopago_signature(headers: Dict[str, str], body: bytes) -> bool:
    """Verify Mercado Pago webhook signature if configured"""
    if not settings.MERCADOPAGO_WEBHOOK_SECRET:
        return True  # No secret configured, accept all

    signature = headers.get("x-signature", "")
    # Si hay secreto configurado, la firma es obligatoria
    if not signature:
        return False  # Missing signature when required

    # Parse signature components
    parts = {}
    for part in signature.split(","):
        key_value = part.strip().split("=", 1)
        if len(key_value) == 2:
            parts[key_value[0]] = key_value[1]
    # Debe existir al menos v1
    received_v1 = parts.get("v1", "")
    if not received_v1:
        return False

    # Calculate expected signature
    expected = hmac.new(
        settings.MERCADOPAGO_WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, received_v1)


# iCal token generation
def generate_ical_token(accommodation_id: int) -> str:
    """Generate a secure token for iCal export"""
    data = f"{accommodation_id}:{datetime.now(UTC).isoformat()}"
    token = hmac.new(settings.ICS_SALT.encode(), data.encode(), hashlib.sha256).hexdigest()
    return token


def verify_ical_token(accommodation_id: int, token: str, stored_token: str) -> bool:
    """Verify an iCal export token"""
    return hmac.compare_digest(token, stored_token)
