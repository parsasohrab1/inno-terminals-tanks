"""Proprietary IP vault — crypto roundtrip + graceful degradation."""
import importlib

import pytest

from app.secure import vault


def test_encrypt_decrypt_roundtrip():
    pw = "a-strong-passphrase-123"
    blob = vault.encrypt_bytes(b"print('secret algorithm')", pw)
    assert b"secret algorithm" not in blob  # ciphertext, not plaintext
    assert vault.decrypt_bytes(blob, pw) == b"print('secret algorithm')"


def test_wrong_key_is_rejected():
    blob = vault.encrypt_bytes(b"payload", "right-key")
    with pytest.raises(vault.VaultLocked):
        vault.decrypt_bytes(blob, "wrong-key")


def test_tamper_is_detected():
    blob = bytearray(vault.encrypt_bytes(b"payload", "k"))
    blob[-1] ^= 0x01
    with pytest.raises((vault.VaultLocked, ValueError)):
        vault.decrypt_bytes(bytes(blob), "k")


def test_loader_returns_none_when_locked(monkeypatch):
    import app.secure as secure

    monkeypatch.setattr(vault, "_passphrase", lambda: None)
    importlib.reload(secure)
    # plaintext dev copies may exist in this tree; if so the loader legitimately
    # returns a module. The contract we assert: no key AND no plaintext -> None.
    monkeypatch.setattr(secure, "MODULES_DIR", secure.MODULES_DIR / "does-not-exist")
    secure._cache.clear()
    assert secure.load("gnn_leak") is None
