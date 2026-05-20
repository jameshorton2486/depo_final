from __future__ import annotations

import importlib.util
from pathlib import Path

from backend.config import settings
from backend.database.init_db import database_status, initialize_database

REQUIRED_IMPORTS = [
    "fastapi",
    "uvicorn",
    "numpy",
    "soundfile",
]
REQUIRED_FRONTEND_FILES = [
    Path("frontend/index.html"),
    Path("frontend/screens/stage_1_intake.html"),
    Path("frontend/screens/stage_2_transcripts.html"),
    Path("frontend/screens/stage_3_workspace.html"),
    Path("frontend/screens/stage_4_insertions.html"),
    Path("frontend/screens/stage_6_export.html"),
]


def run_startup_validation(database_path: Path | None = None) -> dict[str, object]:
    resolved_database = initialize_database(database_path)
    missing_imports = [name for name in REQUIRED_IMPORTS if importlib.util.find_spec(name) is None]
    missing_files = [
        str(settings.project_root / relative_path)
        for relative_path in REQUIRED_FRONTEND_FILES
        if not (settings.project_root / relative_path).exists()
    ]
    required_roots = {
        "frontend_root": settings.frontend_root,
        "data_root": settings.data_root,
        "cases_root": settings.cases_root,
        "sqlite_root": settings.sqlite_root,
    }
    missing_roots = [name for name, path in required_roots.items() if not Path(path).exists()]
    db_state = database_status(resolved_database)
    checks = {
        "database_initialized": db_state["tables_initialized"],
        "database_path_exists": Path(resolved_database).exists(),
        "required_imports_present": not missing_imports,
        "frontend_files_present": not missing_files,
        "required_roots_present": not missing_roots,
    }
    return {
        "ok": all(bool(value) for value in checks.values()),
        "checks": checks,
        "database_path": str(resolved_database),
        "missing_imports": missing_imports,
        "missing_frontend_files": missing_files,
        "missing_roots": missing_roots,
    }
