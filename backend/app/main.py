"""MOVA Backend — FastAPI application entry point.

Launches with:  uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

ARCHITECTURE:
- FastAPI provides async request handling, built-in Pydantic v2 validation,
  OpenAPI docs at /docs, and CORS middleware.
- We use lifespan events for clean startup/shutdown of shared resources.
- The Gemini client is a singleton created once at startup.
- Rate limiting, request dedup, and session management are all in-memory
  (suitable for single-process dev; swap for Redis in production).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware import RequestLoggingMiddleware
from app.routers import chat, health
from app.services.gemini import gemini_service

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("mova")


# ── Lifespan handler ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle.

    Startup: Pre-heat the Gemini service so the first request isn't slow.
    Shutdown: No special cleanup needed (in-memory state discarded).
    """
    logger.info("Starting MOVA backend (model=%s)", settings.gemini_model)
    gemini_service.load_system_prompt()
    logger.info("System prompt loaded (%d chars)", len(gemini_service._system_prompt))
    yield
    logger.info("Shutting down MOVA backend")


# ── App factory ──────────────────────────────────────────────────────────
app = FastAPI(
    title="MOVA — Transport & Mobility AI",
    description="Backend API for the Transport & Mobility AI assistant",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────
# Allow the Vite dev server and production builds on common ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Middleware ────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(chat.router)


# ── Root endpoint ────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": "MOVA",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ── Entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
