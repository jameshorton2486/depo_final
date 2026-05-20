@echo off
setlocal
set PYTHON_BIN=.\.venv\Scripts\python.exe

echo [1/6] Verifying imports...
%PYTHON_BIN% -c "import backend.app; import backend.parsers.nod_parser; import backend.services.intake_service; import backend.preprocessing.preprocessing_service; import backend.deepgram.prerecorded; import backend.transcript.transcript_service; import backend.review.transcript_query_service; import backend.review.correction_engine; import backend.realtime.realtime_service; import backend.legal_review.review_dashboard; import backend.system.health_monitor; import desktop.launcher"
if errorlevel 1 exit /b 1

echo [2/6] Verifying SQLite initialization...
%PYTHON_BIN% -c "from backend.database.init_db import initialize_database; path = initialize_database(); print(path)"
if errorlevel 1 exit /b 1

echo [3/6] Verifying frontend files...
%PYTHON_BIN% -c "from pathlib import Path; required = [Path('frontend/index.html'), Path('frontend/screens/stage_1_intake.html'), Path('frontend/screens/stage_2_transcripts.html'), Path('frontend/screens/stage_3_workspace.html'), Path('frontend/screens/stage_4_insertions.html'), Path('frontend/screens/stage_6_export.html')]; missing = [str(path) for path in required if not path.exists()]; assert not missing, missing"
if errorlevel 1 exit /b 1

echo [4/6] Verifying FastAPI startup, legal review APIs, export endpoints, and realtime lifecycle...
%PYTHON_BIN% scripts\verify_project_runtime.py
if errorlevel 1 exit /b 1

echo [5/6] Verifying desktop launcher wiring...
%PYTHON_BIN% -c "import os; os.environ['DEPO_PRO_LAUNCHER_SMOKE_TEST'] = '1'; import desktop.launcher as launcher; launcher.main(); print('launcher ok')"
if errorlevel 1 exit /b 1

echo [6/6] Verifying database tests...
%PYTHON_BIN% -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 exit /b 1

echo Verification passed.
