# Proprietary IP Vault

The four patentable innovations from SRS appendix 5.3 are shipped as **encrypted
modules**. Their source is never committed in plaintext and is not readable
without the key. Teammates without the key run the platform on open baseline
algorithms — **no loss of availability**, only the patented enhancements are
inactive.

## What is protected

| SRS | Module (encrypted) | Baseline fallback (open) |
|---|---|---|
| FR‑2.8 | `gnn_leak.py.enc` — graph‑NN multi‑tank leak prediction + propagation | `ml/model.py` GBDT + IsolationForest |
| FR‑3.7 | `risk_aware_optimizer.py.enc` — leak‑risk‑aware scheduling | `optimizer._baseline_plan` priority/EDD greedy |
| FR‑2.9 | `twin_leak_sim.py.enc` — physics digital‑twin labelled‑data generator | `digital_twin._lumped_sim` |
| FR‑1.7 | `multimodal_acoustic.py.enc` — acoustic+vibration deep fusion | (none — feature simply inactive) |
| — | `_claims.py.enc` — the patent claim register itself | — |

## Crypto

* **AES‑256‑GCM** (authenticated) per file, key derived with **scrypt**
  (N=2¹⁵) from the passphrase. Wrong key / tampered blob → hard failure.
* Committed artefact: `backend/app/secure/modules/*.py.enc` (base64).
* `.gitignore` blocks every decrypted `*.py` in that directory.

## Key handling

The passphrase is read from, in order:

1. `INNO_IP_KEY` environment variable
2. `ip_key.txt` at the repo root (git‑ignored)

Store it in a secrets manager / CI secret. Never commit it.

## Operations

```bash
cd backend

# key-holder: decrypt for local development (produces git-ignored *.py)
INNO_IP_KEY=... python -m app.secure.manage decrypt

# after editing a proprietary module, re-encrypt and drop the plaintext
INNO_IP_KEY=... python -m app.secure.manage encrypt

# rotate the passphrase across all blobs
python -m app.secure.manage rekey OLD_KEY NEW_KEY

# show state (never prints module contents)
python -m app.secure.manage status
```

## Runtime behaviour

`app.secure.load(name)` decrypts **in memory only** (never writes plaintext) and
returns a live module, or `None` when locked. Every call site degrades to its
baseline. The `/api/v1/admin/ip-vault` endpoint (executive role) reports only
*presence* and *unlock state* — never contents.

## Verifying protection

```bash
cd backend
python -m pytest tests/test_vault.py -q     # crypto roundtrip + rejection
unset INNO_IP_KEY && rm -f app/secure/modules/*.py   # simulate a non-key-holder
python -c "from app import secure; print(secure.load('gnn_leak'))"   # -> None
```
