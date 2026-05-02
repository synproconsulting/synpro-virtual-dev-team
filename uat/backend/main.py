"""
backend/main.py
═══════════════
FastAPI application for the SynPro Virtual Dev Team UAT environment.
Routes are organised in separate router modules (SDT1-47 refactor).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

from auth          import router as auth_router
from profile       import router as profile_router
from notifications import router as notifications_router
from proxy         import router as proxy_router
from pm_agent      import router as pm_agent_router
from manager_agent_router import router as manager_agent_router
from middleware    import RequestLoggingMiddleware
from rate_limiter  import get_limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from config import get_cors_config, CORSConfigError
from security_config import get_jwt_config, SecurityConfigError

# ── Logging setup ─────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")


# ── App setup ─────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    if DATABASE_URL:
        logger.info("✓ Database configured. Use 'alembic upgrade head' to run migrations.")
    else:
        logger.warning("WARNING: DATABASE_URL not set - running without database")
    
    # Validate CORS configuration on startup (SDT1-56)
    try:
        cors_config = get_cors_config()
        logger.info("✓ CORS configuration validated successfully")
    except CORSConfigError as e:
        logger.error(f"❌ CORS configuration error: {e}")
        raise
    
    # Validate JWT/security configuration on startup (SDT1-63)
    try:
        jwt_config = get_jwt_config()
        logger.info("✓ JWT security configuration validated successfully")
        logger.info(f"  - Algorithm: {jwt_config['algorithm']}")
        logger.info(f"  - Token expiry: {jwt_config['expiry_hours']} hours")
    except SecurityConfigError as e:
        logger.error(f"❌ Security configuration error: {e}")
        raise
    
    yield

app = FastAPI(
    title="SynPro Virtual Dev Team - Auth API",
    description="UAT environment for the authentication module",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────────────

# CORS middleware with hardened configuration (SDT1-56)
try:
    cors_config = get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)
    logger.info("CORS middleware configured")
except CORSConfigError as e:
    logger.error(f"Failed to configure CORS: {e}")
    raise

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Routers ───────────────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(notifications_router)
app.include_router(proxy_router)
app.include_router(pm_agent_router)
app.include_router(manager_agent_router)


# ── Root ──────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "auth-api", "version": "1.0.0"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
