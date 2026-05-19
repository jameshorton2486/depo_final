"""Centralized configuration for Depo-Pro backend.

Loads environment variables from .env at project root.
Secrets (API keys) never live in code - only in .env (gitignored).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)

# Server
BACKEND_HOST = os.getenv("DEPOPRO_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("DEPOPRO_BACKEND_PORT", "47853"))

# Paths
UI_ROOT = PROJECT_ROOT / "ui"
DATA_ROOT = PROJECT_ROOT / "data"
DATA_CASES = DATA_ROOT / "cases"

# Debug
DEBUG = os.getenv("DEPOPRO_DEBUG", "0") == "1"

# Future-phase keys (intentionally read here so missing-key errors fail fast at startup)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
