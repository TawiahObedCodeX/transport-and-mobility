"""Chat endpoint — the primary interaction point for MOVA.

POST /chat
{
    "message": "What's the traffic like?",
    "session_id": "abc123"
}

Returns:
{
    "response": "Traffic on I-95 is heavy...",
    "session_id": "abc123"
}

WORKFLOW:
1. Validate request (Pydantic)
2. Check rate limit per IP (sliding window)
3. Check for duplicate request (same message + session in 3s window)
4. Load conversation history from session store
5. Send to Gemini with retry logic
6. Append user message + response to history
7. Return response with session_id
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse
from app.services.gemini import gemini_service
from app.services.session import session_store
from app.utils.rate_limiter import rate_limiter

logger = logging.getLogger("mova.chat")

router = APIRouter(tags=["Chat"])

# Dedup cache: md5 key -> timestamp of last seen request
# Prevents processing the same exact message+session_id twice
_dedup_cache: dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 3.0


def _dedup_key(message: str, session_id: str) -> str:
    raw = f"{session_id}:{message.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _is_duplicate(message: str, session_id: str) -> bool:
    key = _dedup_key(message, session_id)
    now = time.time()
    previous = _dedup_cache.get(key)
    if previous is not None and (now - previous) < DEDUP_WINDOW_SECONDS:
        return True
    _dedup_cache[key] = now
    return False


def _cleanup_dedup_cache() -> None:
    """Remove stale entries older than the dedup window."""
    now = time.time()
    stale = [k for k, v in _dedup_cache.items() if (now - v) > DEDUP_WINDOW_SECONDS]
    for k in stale:
        del _dedup_cache[k]


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        429: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
) -> ChatResponse:
    """Handle a chat message from the user."""
    # Step 1: Rate limiting per client IP
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = await rate_limiter.check(client_ip)
    if not allowed:
        logger.warning("Rate limited: %s", client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after:.0f} seconds.",
        )

    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = body.session_id

    # Step 2: Duplicate request detection
    if _is_duplicate(message, session_id):
        logger.info("Duplicate request ignored: session=%s msg=%.50s", session_id, message)
        raise HTTPException(
            status_code=429,
            detail="Duplicate request. Please wait before sending again.",
        )

    # Step 3: Load conversation history from session store
    history = session_store.get_history(session_id)

    # Step 4: Call Gemini with retry logic
    try:
        response_text = await gemini_service.send_message_async(message, history)
    except ValueError as e:
        logger.error("Invalid request: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error("Gemini error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected Gemini error")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred. Please try again."
        ) from e

    # Step 5: Append both sides of the conversation to history
    session_store.append_to_history(session_id, "user", message)
    session_store.append_to_history(session_id, "model", response_text)

    # Step 6: Periodic cleanup of stale dedup entries
    _cleanup_dedup_cache()

    logger.info("Chat OK: session=%s len=%d", session_id, len(response_text))

    return ChatResponse(response=response_text, session_id=session_id)
