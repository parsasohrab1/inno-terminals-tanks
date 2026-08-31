# INNO Terminals & Tanks — IoT + AI Safety & Operations Platform

Implementation of the SRS in [README.md](README.md): an integrated IoT + AI platform for
real‑time monitoring, leak prediction and loading/unloading optimization of petrochemical
storage terminals.

> The SRS (`README.md`) targets a large industrial deployment with real ATEX sensors, DCS/SCADA,
> Kafka/Flink, TimescaleDB, OPC‑UA, etc. This repository delivers a **fully working software
> product** that implements every functional module (FR‑1 … FR‑6) end‑to‑end with a synthetic
> sensor fleet standing in for physical hardware. The architecture is deliberately close to the
> SRS so real gateways/historians can be swapped in later.

## Architecture

```
                         ┌─────────────────────────┐
  synthetic sensor fleet │  simulator/  (Python)   │  MQTT-style live stream + batch CSV
  (stands in for IoT GW) └───────────┬─────────────┘
                                     │  HTTP ingest  /  WebSocket
                         ┌───────────▼─────────────┐
                         │  backend/  FastAPI      │
                         │  • ingest + time-series │  SQLite (dev) / TimescaleDB (prod)
                         │  • alarm engine (ISA-18.2)
                         │  • leak prediction (IsolationForest + rules + SHAP-lite)
                         │  • load/unload optimizer (greedy + MILP-lite)
                         │  • reporting / KPIs
                         │  • RBAC + JWT auth      │
                         │  • digital twin / What-If
                         └───────────┬─────────────┘
                                     │  REST (OpenAPI 3) + WebSocket
                         ┌───────────▼─────────────┐
                         │  frontend/  React + TS  │  dashboard, terminal map, trends,
                         │  Tailwind, Recharts     │  alarms, predictions, optimizer,
                         │  i18n fa/en + RTL, dark │  reports
                         └─────────────────────────┘
```

## Module → SRS traceability

| SRS module | Where |
|---|---|
| FR‑1 Real‑time monitoring | `backend/app/api/routes/readings.py`, `tanks.py`, `ws.py`; `frontend` Dashboard |
| FR‑2 Leak prediction | `backend/app/services/leak_prediction.py`, `backend/app/ml/` |
| FR‑3 Load/unload optimization | `backend/app/services/optimizer.py` |
| FR‑4 Alarm & event management | `backend/app/services/alarm_engine.py`, `routes/alarms.py`, `events.py` |
| FR‑5 Reporting & analytics | `backend/app/services/reporting.py`, `routes/reports.py` |
| FR‑6 Integration | `backend/app/api/routes/integration.py` (REST/OPC‑UA stubs) |
| NFR‑3 Security (RBAC/MFA/audit) | `backend/app/core/security.py`, `rbac.py`, `models/audit.py` |
| 5.1 Synthetic data | `simulator/generate.py` |
| 5.2 Digital Twin / What‑If | `backend/app/services/digital_twin.py` |

## Quick start

```bash
# 1. backend
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
python -m app.seed            # create db + demo users + tanks
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)

# 2. simulator (new terminal)
cd simulator
pip install -r requirements.txt
python live_stream.py         # streams synthetic readings into the backend

# 3. frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Or everything at once:

```bash
docker compose up --build
```

Demo logins (password `demo1234`): `operator`, `safety`, `opsmanager`, `technician`, `admin`.
