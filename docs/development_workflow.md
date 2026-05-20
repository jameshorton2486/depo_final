# Development Workflow

## Setup

1. Create and activate a Python 3.13 virtual environment.
2. Install backend dependencies from `backend/requirements.txt`.
3. Install optional frontend tooling dependencies if you want to run Prettier and ESLint locally.

## Daily Commands

- Backend dev server:
  - `uvicorn backend.app:app --reload --host 127.0.0.1 --port 8765`
- Desktop launcher:
  - `python desktop/launcher.py`

## Maintenance

- `scripts\\cleanup_python.bat`
- `scripts\\cleanup_frontend.bat`
- `scripts\\verify_project.bat`
- `scripts\\full_maintenance.bat`

## Phase 1 Boundaries

Keep this branch limited to foundation concerns:

- backend shell
- frontend shell
- SQLite initialization
- desktop runtime
- tooling and documentation

Do not introduce realtime, transcription, export, or transcript editing behavior in this phase.
