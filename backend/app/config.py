"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and load all config at startup.
This makes it impossible to run with missing or invalid configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env before reading settings
load_dotenv()


class Settings(BaseSettings):
    """All application configuration in one place.

    Every value has a default or is loaded from the environment.
    Pydantic validates types at startup — no silent None values.
    """

    # ── Gemini ─────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 2048

    # ── Server ─────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 5000
    log_level: str = "INFO"

    # ── CORS ───────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Rate Limiting ──────────────────────────────────
    max_requests_per_minute: int = 10
    max_requests_per_day: int = 1000

    # ── Paths ──────────────────────────────────────────
    prompt_path: Path = Path(__file__).parent.parent.parent / "prompt.md"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_api_key_valid(self) -> bool:
        return bool(self.gemini_api_key) and len(self.gemini_api_key) > 10

    def load_system_prompt(self) -> str:
        """Read the MOVA persona prompt from prompt.md."""
        if not self.prompt_path.exists():
            raise FileNotFoundError(
                f"prompt.md not found at {self.prompt_path}. "
                "Ensure prompt.md exists in the project root."
            )
        return self.prompt_path.read_text(encoding="utf-8")


# Singleton — instantiated once at import time
settings = Settings()
