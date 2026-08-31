"""Runtime loader for encrypted proprietary modules.

``load(name)`` returns a live module decrypted **in memory** (never touching
disk) or ``None`` when the vault is locked / the blob is missing. Callers must
degrade gracefully to their open baseline implementation.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
import types
from pathlib import Path

from app.secure.vault import VaultLocked, decrypt_bytes, key_available

log = logging.getLogger("inno.secure")

MODULES_DIR = Path(__file__).resolve().parent / "modules"
_cache: dict[str, types.ModuleType | None] = {}


def available() -> bool:
    return key_available()


def load(name: str) -> types.ModuleType | None:
    """Load proprietary module ``name`` (without extension). Cached per-process."""
    if name in _cache:
        return _cache[name]

    plain = MODULES_DIR / f"{name}.py"
    enc = MODULES_DIR / f"{name}.py.enc"

    source: str | None = None
    origin = ""
    if plain.exists():  # a key-holder decrypted locally for development
        source = plain.read_text(encoding="utf-8")
        origin = "plaintext"
    elif enc.exists() and key_available():
        try:
            source = decrypt_bytes(enc.read_bytes()).decode("utf-8")
            origin = "vault"
        except VaultLocked as exc:
            log.warning("proprietary module %s locked: %s", name, exc)
    if source is None:
        _cache[name] = None
        return None

    mod_name = f"app.secure._loaded.{name}"
    module = types.ModuleType(mod_name)
    module.__file__ = str(plain if origin == "plaintext" else enc)
    spec = importlib.util.spec_from_loader(mod_name, loader=None)
    module.__spec__ = spec
    try:
        exec(compile(source, module.__file__, "exec"), module.__dict__)  # noqa: S102
    except Exception:  # noqa: BLE001
        log.exception("failed executing proprietary module %s", name)
        _cache[name] = None
        return None
    sys.modules[mod_name] = module
    _cache[name] = module
    log.info("loaded proprietary module '%s' (%s)", name, origin)
    return module


def status() -> dict:
    blobs = sorted(p.name for p in MODULES_DIR.glob("*.py.enc"))
    return {
        "vault_unlocked": key_available(),
        "encrypted_modules": blobs,
        "loaded": sorted(k for k, v in _cache.items() if v is not None),
    }
