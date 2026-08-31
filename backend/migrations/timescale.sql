-- TimescaleDB setup (NFR-2, NFR-6.2). Run once against a fresh Postgres/Timescale
-- database BEFORE `python -m app.seed`. The app's create_all() then fills in the
-- remaining tables; this script upgrades `readings` to a hypertable.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- The app creates `readings` via SQLModel metadata. If you are initialising an
-- empty DB, create a minimal stub so the hypertable exists before ingest; the
-- ORM's create_all() is idempotent and will leave it alone.
CREATE TABLE IF NOT EXISTS readings (
    id                     BIGSERIAL,
    tank_id                INTEGER NOT NULL,
    ts                     TIMESTAMPTZ NOT NULL,
    level                  DOUBLE PRECISION DEFAULT 0,
    temperature            DOUBLE PRECISION DEFAULT 0,
    pressure               DOUBLE PRECISION DEFAULT 0,
    density                DOUBLE PRECISION DEFAULT 0,
    flammable_gas_ppm      DOUBLE PRECISION DEFAULT 0,
    h2s_ppm                DOUBLE PRECISION DEFAULT 0,
    vibration_mm_s         DOUBLE PRECISION DEFAULT 0,
    corrosion_rate_mm_year DOUBLE PRECISION DEFAULT 0,
    acoustic_db            DOUBLE PRECISION DEFAULT 0,
    acoustic_leak_band_ratio DOUBLE PRECISION DEFAULT 0,
    leak_event             INTEGER DEFAULT 0,
    source                 TEXT DEFAULT 'sensor',
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable('readings', 'ts', if_not_exists => TRUE, migrate_data => TRUE);
CREATE INDEX IF NOT EXISTS readings_tank_ts ON readings (tank_id, ts DESC);

-- 7-day continuous aggregate for dashboard trend queries (FR-1.4, FR-5.2)
CREATE MATERIALIZED VIEW IF NOT EXISTS readings_1m
WITH (timescaledb.continuous) AS
SELECT tank_id,
       time_bucket('1 minute', ts) AS bucket,
       avg(level) AS level, avg(pressure) AS pressure,
       avg(flammable_gas_ppm) AS flammable_gas_ppm,
       avg(vibration_mm_s) AS vibration_mm_s,
       max(leak_event) AS leak_event
FROM readings
GROUP BY tank_id, bucket
WITH NO DATA;

-- retention + compression (NFR-6.2: multi-year storage)
SELECT add_retention_policy('readings', INTERVAL '2 years', if_not_exists => TRUE);
ALTER TABLE readings SET (timescaledb.compress, timescaledb.compress_segmentby = 'tank_id');
SELECT add_compression_policy('readings', INTERVAL '14 days', if_not_exists => TRUE);
