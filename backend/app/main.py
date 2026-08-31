"""FastAPI application entrypoint (SW-1: RESTful API + OpenAPI 3.0)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__, secure
from app.api.routes import api_router
from app.config import settings
from app.database import engine, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("inno")

scheduler = BackgroundScheduler(timezone="UTC")


def _scheduled_jobs() -> None:
    from sqlmodel import Session

    from app.services import ingest, leak_prediction

    def leak_sweep() -> None:
        with Session(engine) as s:
            leak_prediction.sweep(s)

    def stale_check() -> None:
        with Session(engine) as s:
            ingest.mark_stale_tanks(s, seconds=180)

    scheduler.add_job(leak_sweep, "interval", minutes=2, id="leak_sweep", max_instances=1)
    scheduler.add_job(stale_check, "interval", seconds=90, id="stale_check", max_instances=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("IP vault: %s", "UNLOCKED" if secure.available() else "locked (baseline algorithms)")
    _scheduled_jobs()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Integrated IoT + AI safety & operations platform for petrochemical "
        "terminals and tanks. Implements SRS v1.0 (README.md)."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "api": settings.api_prefix,
        "ip_vault_unlocked": secure.available(),
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal error"})
