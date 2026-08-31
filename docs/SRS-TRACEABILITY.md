# SRS → implementation traceability

SRS: [`README.md`](../README.md). ✅ implemented · 🟡 partial / stubbed for a
software-only deployment · 🔩 hardware-dependent (interface provided)

## FR-1 Real-time tank monitoring
| Req | Status | Where |
|---|---|---|
| FR-1.1 sensor sampling (level, temp, pressure, density, gas, H2S, vibration, corrosion) | ✅ | `models/reading.py`, `simulator/sensor_fleet.py` |
| FR-1.2 MQTT/OPC-UA/Modbus ingest → time-series DB | 🟡 | HTTP ingest `api/routes/readings.py`; MQTT/OPC-UA are drop-in (`services/ingest.ingest_batch`) |
| FR-1.3 colour-coded dashboard (green/yellow/red) | ✅ | `alarm_engine.AlarmStatusTracker`, frontend `Dashboard`/terminal map |
| FR-1.4 time zoom / trend 1min–1yr | ✅ | `reporting.parameter_trend`, `readings/{id}/trend` |
| FR-1.5 per-parameter configurable thresholds | ✅ | `models/tank.Threshold`, `PUT /tanks/{id}/thresholds` |
| FR-1.6 RCM equipment-health data | ✅ | corrosion/vibration stored; `integration/cmms/work-orders` |
| FR-1.7 acoustic leak sensing + fusion | ✅ (proprietary) | `secure/modules/multimodal_acoustic.py` |

## FR-2 Leak prediction
| FR-2.1 ML anomaly detection (LSTM/IsolationForest/Autoencoder) | ✅ | `ml/model.py` (IsolationForest + GBDT) |
| FR-2.2 train on historical + synthetic, periodic retrain | ✅ | `ml/train.py`, `POST /admin/retrain`, scheduler |
| FR-2.3 ≥30-min horizon, probability + confidence interval | ✅ | `services/leak_prediction.py`, `LeakPrediction` |
| FR-2.4 explainability (SHAP/LIME) | ✅ | permutation contributions in `model._contributions` |
| FR-2.5 real-leak → auto ESD valve isolation (override) | 🟡 | `leak_prediction._issue_esd` (Safety-PLC stub, logged as event) |
| FR-2.6 recall ≥ 0.95, false-alarm < 5% | ✅ | `train.py` threshold tuning; reported in metrics |
| FR-2.7 digital twin + What-If | ✅ | `services/digital_twin.py`, `twin/{id}/simulate` |
| FR-2.8 GNN spatial dependencies | ✅ (proprietary) | `secure/modules/gnn_leak.py` |
| FR-2.9 twin-generated leak training data | ✅ (proprietary) | `secure/modules/twin_leak_sim.py` |

## FR-3 Loading/unloading optimization
| FR-3.1 capacity/flow/safety-constrained plan | ✅ | `services/optimizer.py` |
| FR-3.2 OR / metaheuristic minimisation | ✅ | greedy + 2-opt (baseline); risk-aware (proprietary) |
| FR-3.3 What-If (e.g. pump failure) | ✅ | `optimizer.what_if`, `POST /optimization/what-if` |
| FR-3.4 ERP/MES integration | 🟡 | `integration/erp/orders` REST stub → `Operation` |
| FR-3.5 real-time deviation alarms | ✅ | ingest re-evaluates thresholds during ops |
| FR-3.6 energy term in objective | ✅ | pump hydraulic power in `_energy_kwh` |
| FR-3.7 dynamic leak-risk in objective | ✅ (proprietary) | `secure/modules/risk_aware_optimizer.py` |

## FR-4 Alarm & event management
| FR-4.1 priority queue (critical/high/medium/low) | ✅ | `AlarmSeverity.rank`, `GET /alarms` ordering |
| FR-4.2 multi-channel notify + delivery ack | 🟡 | WebSocket push + ack model; email/SMS are connectors |
| FR-4.3 two-person rule on critical | ✅ | `alarm_engine.acknowledge`, `/alarms/{id}/clear` guard |
| FR-4.4 full signed event record | ✅ | `models/event.py`, HMAC `digital_signature` |
| FR-4.5 intelligent suppression of duplicate cause | ✅ | `dedup_key` + `_apply_isa_18_2` root-cause linking |
| FR-4.6 ISA-18.2 rationalisation (≤6/op/hr) | ✅ | `alarm_engine.operator_alarm_rate`, flood suppression |

## FR-5 Reporting & analytics
| FR-5.1 daily/weekly/monthly KPI reports | ✅ | `reporting.kpi_summary`, `GET /reports/kpi` |
| FR-5.2 interactive management dashboard | ✅ | frontend `Reports`, Recharts trends |
| FR-5.3 advanced historical search | 🟡 | time/tank/parameter filters on readings & alarms |
| FR-5.4 API RP 2350 / IEC 61511 compliance report | ✅ | `reporting.compliance_report` |

## FR-6 Integration
| FR-6.1 OPC-UA to DCS/SCADA | 🟡 | address-space projection `integration/opcua/nodes` |
| FR-6.2 CMMS preventive work orders | ✅ | `integration/cmms/work-orders` |
| FR-6.3 ERP REST | 🟡 | `integration/erp/orders` |
| FR-6.4 ISA-95 hierarchy | ✅ | `integration/isa95/equipment-hierarchy` |

## Non-functional
| NFR-1 latency/throughput | 🟡 | async ingest, batch cap; single-node (Kafka/Flink for scale) |
| NFR-2 reliability / redundancy / RPO-RTO | 🟡 | stateless API, TimescaleDB; HA is deployment concern |
| NFR-3.1 RBAC + MFA | ✅ | `core/security.py`, `api/deps.require_roles`, TOTP |
| NFR-3.2 encryption in transit/at rest | 🟡 | TLS at ingress; IP vault AES-256; column crypto = deployment |
| NFR-3.3 IEC 62443 segmentation / IDS | 🔩 | network-layer concern; documented |
| NFR-3.4 full audit log | ✅ | `core/audit.py` hash-chained `AuditLog` |
| NFR-4.1 microservice-ready | 🟡 | modular services; single deployable for now |
| NFR-5 portability (cloud/on-prem, browsers, mobile) | ✅ | Docker, responsive RTL/LTR UI |
| NFR-7 ATEX/API RP 2350/IEC 61511 | 🔩/✅ | overfill limits + ESD logging in software; certs are hardware |
