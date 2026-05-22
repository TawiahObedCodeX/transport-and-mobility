"""Health check endpoint — used by frontend to verify backend is alive.

GET /health returns:
{
    "status": "ok",
    "version": "1.0.0",
    "session_count": 5
}

Also serves as a readiness probe for container orchestration.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse
from app.services.session import session_store

logger = logging.getLogger("mova.health")

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return server status and basic metrics."""
    return HealthResponse(
        status="ok",
        session_count=session_store.count,
        api_key_configured=settings.is_api_key_valid,
    )
