"""
Virtual IoT Security Laboratory — Backend Application Entry Point

This module initializes the FastAPI application, configures middleware,
registers routers, and manages application lifecycle events.
"""
import sys
from pathlib import Path

# Ensure both project root and backend directory are in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND = Path(__file__).resolve().parent.parent
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.database import connect_to_mongodb, close_mongodb_connection
from app.core.mqtt_client import connect_mqtt, disconnect_mqtt
from app.api.routes import devices, telemetry, security, scenarios, lab, audit, investigation
from app.api.websocket import router as websocket_router
from app.core.middleware import SecurityHeadersMiddleware


# Configure structured logging before anything else
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    Handles startup and shutdown of all background services.
    """
    # --- Startup ---
    logger.info(
        "application_starting",
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )

    # Connect to MongoDB
    await connect_to_mongodb()
    logger.info("database_connected", uri=settings.MONGODB_URI)

    # Connect to MQTT broker
    await connect_mqtt()
    logger.info(
        "mqtt_connected",
        host=settings.MQTT_BROKER_HOST,
        port=settings.MQTT_BROKER_PORT,
    )

    logger.info("application_ready")
    yield

    # --- Shutdown ---
    logger.info("application_shutting_down")

    await disconnect_mqtt()
    logger.info("mqtt_disconnected")

    await close_mongodb_connection()
    logger.info("database_disconnected")

    logger.info("application_stopped")


# ============================================================
# FastAPI Application
# ============================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Virtual IoT Security Laboratory — A software-only IoT security "
        "simulation environment for device management, telemetry, security "
        "event detection, and attack scenario simulation."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ============================================================
# Middleware
# ============================================================

# CORS — allow configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)

# Trusted hosts — lock down in production only
if settings.APP_ENV == "production" and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

# ============================================================
# Routers
# ============================================================
API_PREFIX = "/api"

app.include_router(devices.router, prefix=API_PREFIX)
app.include_router(telemetry.router, prefix=API_PREFIX)
app.include_router(security.router, prefix=API_PREFIX)
app.include_router(scenarios.router, prefix=API_PREFIX)
app.include_router(lab.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(websocket_router)
app.include_router(investigation.router, prefix="/api")

# ============================================================
# Health / Root
# ============================================================
@app.get("/api/info", tags=["Health"])
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns status of the application and dependent services.
    """
    from app.core.database import get_database_status
    from app.core.mqtt_client import get_mqtt_status

    db_status = await get_database_status()
    mqtt_status = get_mqtt_status()

    overall = "healthy" if db_status["connected"] else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "database": db_status,
            "mqtt": mqtt_status,
        },
    }


# ============================================================
# Static Frontend Serving (All-in-One Deployment Mode)
# ============================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi import HTTPException

@app.head("/", include_in_schema=False)
@app.head("/api/health", include_in_schema=False)
@app.head("/api/info", include_in_schema=False)
async def head_health_probe():
    return Response(status_code=200)

_FRONTEND_CANDIDATES = [
    Path("/app/frontend_dist"),  # Inside Docker container
    _ROOT / "frontend" / "dist",  # Local build
]

_frontend_dist = None
for _cand in _FRONTEND_CANDIDATES:
    if _cand.exists() and (_cand / "index.html").exists():
        _frontend_dist = _cand
        break

if _frontend_dist:
    if (_frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = _frontend_dist / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(_frontend_dist / "index.html")
else:
    @app.get("/", tags=["Health"])
    async def root():
        return await api_info()

