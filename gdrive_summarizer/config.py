"""Centralised configuration loaded from environment / .env file."""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


# ── OpenRouter ────────────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"

# Model used for pure-text requests (summarisation, etc.)
TEXT_MODEL: str = os.getenv("TEXT_MODEL", "google/gemma-3-27b-it:free")

# Model used for vision / multimodal requests (image description).
# Primary model from .env; fallback chain tried on 403 / rate-limit.
VISION_MODEL: str = os.getenv("VISION_MODEL", "google/gemma-3-27b-it:free")

# Fallback chain for vision when the primary model is blocked / rate-limited.
# Comma-separated in .env, or sensible defaults.
_vision_fb = os.getenv(
    "VISION_FALLBACK_MODELS",
    "mistralai/mistral-small-3.1-24b-instruct:free,"
    "google/gemma-3-12b-it:free,"
    "nvidia/nemotron-nano-12b-v2-vl:free,"
    "google/gemini-2.5-flash:free",
)
VISION_FALLBACK_MODELS: List[str] = [
    m.strip() for m in _vision_fb.split(",") if m.strip()
]

# ── Paths ─────────────────────────────────────────────────────────────
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")

# ── Rate-limit helpers ────────────────────────────────────────────────
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "5.0"))  # seconds
