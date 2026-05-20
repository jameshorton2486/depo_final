# DEPO-PRO Phase 1 Architecture

## Scope

Phase 1 establishes the local-first application foundation for a legal deposition production workspace. It includes:

- a FastAPI backend shell
- a static HTML/CSS/JavaScript frontend shell
- SQLite initialization via `sqlite3`
- a PyWebView desktop runtime
- shared configuration and maintenance tooling

This phase does not include transcription, review, export generation, Deepgram integration, realtime systems, or transcript editing.

## Runtime Layout

- `backend/app.py` exposes `/api/health` and serves the frontend shell.
- `backend/database/init_db.py` creates the Phase 1 starter tables in `data/sqlite/depo_pro.db`.
- `frontend/` contains a stage-based shell with dynamic screen loading and persistent local state.
- `desktop/launcher.py` starts FastAPI on a background thread and opens the local UI in PyWebView.

## Data Model

The initial schema is intentionally minimal:

- `cases`
- `sessions`
- `transcript_assets`

These tables establish the relationships needed for later deposition workflow phases without introducing later-phase business rules.

## Frontend Foundation

The UI provides:

- left navigation rail
- top workspace header
- six-stage pipeline indicator
- RAW and WORKING layer badges
- responsive dark/light theme toggle
- stage routing and screen caching

## Extension Path

Later phases can add:

- API routers under `backend/api/`
- domain logic under `backend/services/`
- transcript-specific processing under `backend/transcript/`
- preprocessing and Deepgram integrations in their reserved packages
