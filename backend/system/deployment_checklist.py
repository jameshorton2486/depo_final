from __future__ import annotations

from backend.system.startup_validation import run_startup_validation


def build_deployment_checklist() -> dict[str, object]:
    startup = run_startup_validation()
    items = [
        {
            "name": "startup_validation",
            "status": "ok" if startup["ok"] else "error",
            "details": startup["checks"],
        },
        {
            "name": "database_initialized",
            "status": "ok" if startup["checks"]["database_initialized"] else "error",
        },
        {
            "name": "frontend_assets_present",
            "status": "ok" if startup["checks"]["frontend_files_present"] else "error",
        },
    ]
    return {
        "ready": all(item["status"] == "ok" for item in items),
        "items": items,
    }
