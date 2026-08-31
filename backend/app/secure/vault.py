"""Cryptographic vault for proprietary / patentable modules (SRS appendix 5.3).

Design goals
------------
* Plaintext source of the patented algorithms is NEVER committed to git
  (see repo .gitignore) and never written to disk by the running service.
* Only ``*.py.enc`` blobs are committed. They are useless without the key.
* The key is a passphrase supplied out-of-band via the ``INNO_IP_KEY`` env var
  (or ``ip_key.txt`` at the repo root). Teammates without the key run the
  platform on open baseline algorithms with no loss of availability.

Crypto: AES-256-GCM (authenticated) with a scrypt-derived key.
"""
from __future__ import annotations

import base64
import os
import struct
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from app.config import REPO_DIR, settings

MAGIC = b"INNOIP01"
# Non-secret KDF salt. Rotating this invalidates every existing .enc blob.
_SALT = b"inno-terminals-tanks::ip-vault::v1"
_SCRYPT_N = 2**15
_SCRYPT_R = 8
_SCRYPT_P = 1


class VaultLocked(RuntimeError):
    """Raised when a proprietary module is requested but no valid key is present."""


def _passphrase() -> str | None:
    if settings.ip_key:
        return settings.ip_key
    env = os.environ.get("INNO_IP_KEY")
    if env:
        return env
    key_file = REPO_DIR / "ip_key.txt"
    if key_file.exists():
        txt = key_file.read_text(encoding="utf-8").strip()
        if txt:
            return txt
    return None


def key_available() -> bool:
    return _passphrase() is not None


def _derive_key(passphrase: str) -> bytes:
    kdf = Scrypt(salt=_SALT, length=32, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_bytes(plaintext: bytes, passphrase: str) -> bytes:
    key = _derive_key(passphrase)
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext, MAGIC)
    blob = MAGIC + struct.pack("<H", len(nonce)) + nonce + ct
    return base64.b64encode(blob)


def decrypt_bytes(blob_b64: bytes, passphrase: str | None = None) -> bytes:
    passphrase = passphrase or _passphrase()
    if not passphrase:
        raise VaultLocked("INNO_IP_KEY is not set — proprietary module unavailable")
    raw = base64.b64decode(blob_b64)
    if raw[:8] != MAGIC:
        raise ValueError("not an INNO IP vault blob")
    (nlen,) = struct.unpack("<H", raw[8:10])
    nonce = raw[10 : 10 + nlen]
    ct = raw[10 + nlen :]
    key = _derive_key(passphrase)
    try:
        return AESGCM(key).decrypt(nonce, ct, MAGIC)
    except InvalidTag as exc:  # wrong key or tampered blob
        raise VaultLocked("proprietary module failed to decrypt (wrong INNO_IP_KEY?)") from exc


def encrypt_file(src: Path, passphrase: str) -> Path:
    dst = src.with_suffix(src.suffix + ".enc")
    dst.write_bytes(encrypt_bytes(src.read_bytes(), passphrase))
    return dst


def decrypt_file(enc: Path, passphrase: str | None = None) -> Path:
    dst = enc.with_suffix("")  # drop .enc
    dst.write_bytes(decrypt_bytes(enc.read_bytes(), passphrase))
    return dst
