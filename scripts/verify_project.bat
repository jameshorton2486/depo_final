@echo off
setlocal
set PYTHON_BIN=.\.venv\Scripts\python.exe

echo [1/6] Verifying imports...
%PYTHON_BIN% -c "import backend.app; import backend.parsers.nod_parser; import backend.services.intake_service; import desktop.launcher"
if errorlevel 1 exit /b 1

echo [2/6] Verifying SQLite initialization...
%PYTHON_BIN% -c "from backend.database.init_db import initialize_database; path = initialize_database(); print(path)"
if errorlevel 1 exit /b 1

echo [3/6] Verifying frontend files...
%PYTHON_BIN% -c "from pathlib import Path; required = [Path('frontend/index.html'), Path('frontend/screens/stage_1_intake.html'), Path('frontend/screens/stage_6_export.html')]; missing = [str(path) for path in required if not path.exists()]; assert not missing, missing"
if errorlevel 1 exit /b 1

echo [4/6] Verifying FastAPI startup, intake parsing, and DB status...
%PYTHON_BIN% -c "import json, subprocess, time, urllib.request; process = subprocess.Popen(['.\\\\.venv\\\\Scripts\\\\python.exe', '-m', 'uvicorn', 'backend.app:app', '--host', '127.0.0.1', '--port', '8765']); time.sleep(2); health = json.loads(urllib.request.urlopen('http://127.0.0.1:8765/api/health').read().decode('utf-8')); db_status = json.loads(urllib.request.urlopen('http://127.0.0.1:8765/api/db/status').read().decode('utf-8')); stage1 = urllib.request.urlopen('http://127.0.0.1:8765/screens/stage_1_intake.html').status; payload = json.dumps({'pasted_text': 'DELIA GARZA\\nv.\\nHOME DEPOT U.S.A., INC.\\nCAUSE NO. 25-cv-00598-OLG\\nDate: 04/30/2026\\nTime: 1:30 PM\\nNotice of deposition of Heath Thomas\\nSteven A. Nunez\\nservice@brainspine-law.com\\nATTORNEYS FOR PLAINTIFF', 'intake_metadata': {'source_document': 'verify-intake.txt'}}).encode('utf-8'); request = urllib.request.Request('http://127.0.0.1:8765/api/intake/parse', data=payload, headers={'Content-Type': 'application/json'}, method='POST'); parsed = json.loads(urllib.request.urlopen(request).read().decode('utf-8')); persisted_url = 'http://127.0.0.1:8765/api/intake/' + str(parsed['case_id']); persisted = json.loads(urllib.request.urlopen(persisted_url).read().decode('utf-8')); process.terminate(); process.wait(timeout=10); assert health['status'] == 'ok'; assert db_status['database'] == 'connected'; assert db_status['tables_initialized'] is True; assert stage1 == 200; assert parsed['keyterms']['term_count'] >= 1; assert parsed['phonetics']['generated'] is not None; assert persisted['case']['id'] == parsed['case_id']; print(health); print(db_status); print(parsed['case_id'])"
if errorlevel 1 exit /b 1

echo [5/6] Verifying desktop launcher wiring...
%PYTHON_BIN% -c "import os; os.environ['DEPO_PRO_LAUNCHER_SMOKE_TEST'] = '1'; import desktop.launcher as launcher; launcher.main(); print('launcher ok')"
if errorlevel 1 exit /b 1

echo [6/6] Verifying database tests...
%PYTHON_BIN% -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 exit /b 1

echo Verification passed.
