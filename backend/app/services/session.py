"""Session manager for MOVA conversations.

Stores conversation histories keyed by session_id.
Current implementation uses an in-memory dict with periodic cleanup.
Drop-in replaceable with Redis for multi-worker deployments.

Each session stores:
{
    "history": [
        {"role": "user",  "parts": [{"text": "..."}]},
        {"role": "model", "parts": [{"text": "..."}]}
    ],
    "created_at": timestamp,
    "last_active": timestamp
}
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("mova.session")

# Maximum session age before cleanup (24 hours)
MAX_SESSION_AGE_SECONDS = 86400
# Maximum messages per session to prevent unbounded token growth
MAX_HISTORY_LENGTH = 50


class SessionStore:
    """In-memory session store with automatic expiry.

    Thread-safe for asyncio via the GIL (single-process).
    For multi-process deployments, swap this for a Redis-backed store.
    """

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def get_or_create(self, session_id: str) -> dict[str, Any]:
        """Return the session dict, creating it if it doesn't exist."""
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "history": [],
                "created_at": now,
                "last_active": now,
            }
        else:
            self._sessions[session_id]["last_active"] = now
        return self._sessions[session_id]

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Return the conversation history list for a session."""
        session = self.get_or_create(session_id)
        return session["history"]

    def append_to_history(
        self,
        session_id: str,
        role: str,
        text: str,
    ) -> None:
        """Append a single message to the session history.

        Also enforces the maximum history length by dropping the
        oldest messages when the limit is exceeded.
        """
        session = self.get_or_create(session_id)
        session["history"].append({
            "role": role,
            "parts": [{"text": text}],
        })
        # Trim oldest messages when history gets too long
        if len(session["history"]) > MAX_HISTORY_LENGTH:
            excess = len(session["history"]) - MAX_HISTORY_LENGTH
            session["history"] = session["history"][excess:]
            logger.info("Trimmed %d old messages from session %s", excess, session_id)

    def delete(self, session_id: str) -> None:
        """Remove a session entirely."""
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """Remove sessions older than MAX_SESSION_AGE_SECONDS.

        Returns the number of cleaned-up sessions.
        Useful as a background task.
        """
        now = time.time()
        cutoff = now - MAX_SESSION_AGE_SECONDS
        expired = [
            sid
            for sid, data in self._sessions.items()
            if data["last_active"] < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
        if expired:
            logger.info("Cleaned up %d expired sessions", len(expired))
        return len(expired)

    @property
    def count(self) -> int:
        return len(self._sessions)

    @property
    def active_sessions(self) -> dict[str, dict[str, Any]]:
        return self._sessions


# Singleton
session_store = SessionStore()
