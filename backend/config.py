from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "DEPO-PRO"
    app_version: str = "0.1"
    backend_host: str = os.getenv("DEPO_PRO_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("DEPO_PRO_PORT", "8765"))
    debug: bool = os.getenv("DEPO_PRO_DEBUG", "0") == "1"
    transcribe_mock: bool = os.getenv("DEPO_PRO_TRANSCRIBE_MOCK", "0") == "1"
    deepgram_api_key: str | None = os.getenv("DEEPGRAM_API_KEY")
    project_root: Path = PROJECT_ROOT
    frontend_root: Path = PROJECT_ROOT / "frontend"
    data_root: Path = PROJECT_ROOT / "data"
    cases_root: Path = PROJECT_ROOT / "data" / "cases"
    sqlite_root: Path = PROJECT_ROOT / "data" / "sqlite"
    database_path: Path = PROJECT_ROOT / "data" / "sqlite" / "depo_pro.db"


settings = Settings()
