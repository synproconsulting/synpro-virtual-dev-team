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

from auth          import router as auth_router
from profile       import router as profile_router
from notifications import router as notifications_router
from proxy         import router as proxy_router
from pm_agent      import router as pm_agent_router
from manager_agent_router import router as manager_agent_router
from middleware    import RequestLoggingMiddleware
from rate_limiter  import get_limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from config        import settings

# ── Config ────────────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")


# ── App setup ─────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    if DATABASE_URL:
        print("✓ Database configured. Use 'alembic upgrade head' to run migrations.")
    else:
        print("WARNING: DATABASE_URL not set - running without database")
    
    # Validate configuration on startup
    try:
        settings.validate()
        allowed_origins = settings.get_allowed_origins()
        print(f"✓ CORS configured with allowed origins: {allowed_origins}")
    except ValueError as e:
        print(f"ERROR: Configuration validation failed: {e}")
        raise
    
    yield

app = FastAPI(
    title="SynPro Virtual Dev Team - Auth API",
    description="UAT environment for the authentication module",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────────────

# CORS middleware with hardened configuration
allowed_origins = settings.get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
