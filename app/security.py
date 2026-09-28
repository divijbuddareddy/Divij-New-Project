import os
import base64
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Truncate to 72 bytes safely as per bcrypt specification
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# AES-256-GCM Token Encryption for secrets & OAuth tokens
def _get_aes_key() -> bytes:
    key_hex = settings.ENCRYPTION_KEY
    if len(key_hex) == 64:
        return bytes.fromhex(key_hex)
    raw = key_hex.encode("utf-8")
    return (raw * 32)[:32]

def encrypt_token(plain_token: str) -> Dict[str, str]:
    """Encrypts a sensitive token using AES-256-GCM and returns ciphertext + iv (nonce)."""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_token.encode("utf-8"), None)
    return {
        "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        "iv": base64.b64encode(nonce).decode("utf-8")
    }

def decrypt_token(ciphertext_b64: str, iv_b64: str) -> str:
    """Decrypts AES-256-GCM ciphertext."""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    ciphertext = base64.b64decode(ciphertext_b64)
    nonce = base64.b64decode(iv_b64)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode("utf-8")
