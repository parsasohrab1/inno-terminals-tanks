from fastapi import APIRouter

from app.api.routes import (
    admin, alarms, auth, events, integration, optimization,
    predictions, readings, reports, tanks, twin, ws,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tanks.router, prefix="/tanks", tags=["tanks"])
api_router.include_router(readings.router, prefix="/readings", tags=["monitoring"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["leak-prediction"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
api_router.include_router(twin.router, prefix="/twin", tags=["digital-twin"])
api_router.include_router(reports.router, prefix="/reports", tags=["reporting"])
api_router.include_router(integration.router, prefix="/integration", tags=["integration"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(ws.router, tags=["realtime"])
