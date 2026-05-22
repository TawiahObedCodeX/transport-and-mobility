"""Pydantic v2 schemas for request validation and response serialization.

All API inputs and outputs are defined here with strict validation.
Invalid requests are rejected with clear error messages before
reaching any service logic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for POST /chat requests.

    Validates that:
    - message is present and non-empty
    - session_id is present (or we generate one server-side)
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's message to MOVA",
        examples=["What is a BRT system?"],
    )
    session_id: str = Field(
        "",
        description="Unique conversation identifier (generated server-side if empty)",
        examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )


class ChatResponse(BaseModel):
    """Schema for POST /chat responses."""

    response: str = Field(..., description="MOVA's reply text")
    session_id: str = Field(..., description="The session ID for this conversation")
    remaining: int = Field(0, description="Remaining requests in the current rate window")


class ErrorResponse(BaseModel):
    """Schema for all error responses — consistent format everywhere."""

    error: str = Field(..., description="Human-readable error message")
    code: int = Field(..., description="HTTP status code")
    retry_after: int | None = Field(None, description="Seconds to wait before retrying")


class HealthResponse(BaseModel):
    """Schema for GET /health responses."""

    status: str = Field("ok", description="Server health status")
    agent: str = Field("MOVA", description="Agent name")
    version: str = Field("2.0.0", description="API version")
    session_count: int = Field(0, description="Active session count")
    api_key_configured: bool = Field(False, description="Whether the Gemini API key is set")
