# DEPO-PRO

DEPO-PRO Phase 1 establishes the local-first foundation for a legal deposition production workspace. This phase includes the frontend shell, backend shell, SQLite initialization, PyWebView desktop runtime, shared configuration, and development tooling only.

## Environment Setup

DEPO-PRO Phase 1 targets:

- Windows 11
- Python 3.13
- PyCharm or another local Python IDE

Create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

Optional frontend tooling for maintenance scripts:

```powershell
npm install --save-dev prettier eslint
```

## Launching the Application

Run the backend directly:

```powershell
uvicorn backend.app:app --host 127.0.0.1 --port 8765 --reload
```

Launch the desktop shell:

```powershell
python desktop\launcher.py
```

The backend serves the static frontend and initializes `data\sqlite\depo_pro.db` on startup.

## Project Layout

```text
depo_final/
├── backend/
├── desktop/
├── frontend/
├── data/
├── docs/
├── scripts/
├── tests/
├── pyproject.toml
└── README.md
```

## Maintenance Scripts

Run Python formatting and lint fixes:

```powershell
scripts\cleanup_python.bat
```

Run frontend formatting and lint fixes:

```powershell
scripts\cleanup_frontend.bat
```

Run project verification:

```powershell
scripts\verify_project.bat
```

Run all maintenance and verification:

```powershell
scripts\full_maintenance.bat
```

## Phase 1 Scope

This branch stops at:

- architecture shell
- frontend shell
- backend shell
- SQLite initialization
- desktop launcher
- maintenance tooling

It does not include transcription, transcript review, DOCX export, Deepgram integration, AI cleanup, or realtime systems.
