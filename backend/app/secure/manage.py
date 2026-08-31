"""CLI to manage the proprietary IP vault.

    python -m app.secure.manage encrypt      # *.py  -> *.py.enc  (then delete plaintext)
    python -m app.secure.manage decrypt      # *.py.enc -> *.py    (key-holders only)
    python -m app.secure.manage status
    python -m app.secure.manage rekey OLD NEW

The passphrase comes from INNO_IP_KEY (env) or ip_key.txt at the repo root.
"""
from __future__ import annotations

import sys
from pathlib import Path

from app.config import REPO_DIR
from app.secure import MODULES_DIR, status
from app.secure.vault import decrypt_bytes, encrypt_bytes


def _passphrase(argv_val: str | None = None) -> str:
    import os

    pw = argv_val or os.environ.get("INNO_IP_KEY")
    if not pw:
        kf = REPO_DIR / "ip_key.txt"
        if kf.exists():
            pw = kf.read_text(encoding="utf-8").strip()
    if not pw:
        sys.exit("no passphrase: set INNO_IP_KEY or create ip_key.txt at repo root")
    return pw


def cmd_encrypt() -> None:
    pw = _passphrase()
    n = 0
    for src in sorted(MODULES_DIR.glob("*.py")):
        if src.name == "__init__.py":
            continue
        enc = src.with_suffix(".py.enc")
        enc.write_bytes(encrypt_bytes(src.read_bytes(), pw))
        src.unlink()
        print(f"encrypted  {src.name} -> {enc.name}  (plaintext removed)")
        n += 1
    print(f"done: {n} module(s)")


def cmd_decrypt() -> None:
    pw = _passphrase()
    n = 0
    for enc in sorted(MODULES_DIR.glob("*.py.enc")):
        dst = enc.with_suffix("")
        dst.write_bytes(decrypt_bytes(enc.read_bytes(), pw))
        print(f"decrypted  {enc.name} -> {dst.name}")
        n += 1
    print(f"done: {n} module(s) — remember these are git-ignored")


def cmd_status() -> None:
    for k, v in status().items():
        print(f"{k:20} {v}")


def cmd_rekey(old: str, new: str) -> None:
    for enc in sorted(MODULES_DIR.glob("*.py.enc")):
        plain = decrypt_bytes(enc.read_bytes(), old)
        enc.write_bytes(encrypt_bytes(plain, new))
        print(f"rekeyed   {enc.name}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    cmd, *rest = args
    if cmd == "encrypt":
        cmd_encrypt()
    elif cmd == "decrypt":
        cmd_decrypt()
    elif cmd == "status":
        cmd_status()
    elif cmd == "rekey" and len(rest) == 2:
        cmd_rekey(rest[0], rest[1])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
