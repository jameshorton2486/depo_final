# Depo-Pro

Local Streamlit-replacement desktop application for Texas court reporter deposition workflow. Static HTML/CSS/JS frontend in a PyWebView desktop shell, with a FastAPI backend and SQLite database (to be added in Phase B).

## Architecture

- Frontend: HTML, CSS, JavaScript (no build step)
- Desktop shell: PyWebView
- Backend: FastAPI (Phase B)
- Database: SQLite (Phase B)
- AI: Deepgram, OpenAI/Anthropic (Phase C)

## Project Structure

```text
depo_final/
├── main.py              Desktop launcher
├── requirements.txt
├── ui/
│   ├── index.html       Shell with 6-stage navigation
│   ├── screens/         One HTML file per stage (Phase A.1)
│   └── assets/
│       ├── css/
│       └── js/
├── backend/             FastAPI app (Phase B)
├── data/
│   └── cases/           Per-case folders
└── docs/                Architecture, schema, phase notes
```

## Running locally

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

A native desktop window opens displaying the workspace. Right-click -> Inspect for Chromium DevTools (`debug=True`).

## Phase Status

- Phase A.0: Project scaffold, desktop shell launches ✓
- Phase A.1: Screen decomposition + router (pending)
- Phase A.2: Extract shared CSS/JS (pending)
- Phase A.3: Per-screen polish + schema doc (pending)
- Phase B: FastAPI backend + SQLite (pending)
- Phase C: Deepgram, AI cleanup, export (pending)
- Phase D: Word-timing sync, certification, advanced review (pending)
