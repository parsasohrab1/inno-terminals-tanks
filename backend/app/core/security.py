"""Auth primitives: password hashing, JWT, TOTP MFA, digital signatures."""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# pbkdf2_sha256: pure-python, no native bcrypt build headaches on Windows.
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=180_000)


def hash_password(pw: str) -> str:
    return _pwd.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return _pwd.verify(pw, hashed)
    except ValueError:
        return False


def create_access_token(subject: str, role: str, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


# --- MFA (TOTP) — NFR-3.1 ---
def new_mfa_secret() -> str:
    return pyotp.random_base32()


def mfa_provisioning_uri(secret: str, username: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=settings.mfa_issuer)


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


# --- digital signatures for alarm acks / event records (FR-4.4) ---
def digital_signature(*parts: object) -> str:
    msg = "|".join(str(p) for p in parts).encode()
    return hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()


def chain_hash(prev_hash: str, payload: str) -> str:
    return hashlib.sha256(f"{prev_hash}:{payload}".encode()).hexdigest()
