@echo off
setlocal
set PYTHON_BIN=.\.venv\Scripts\python.exe
%PYTHON_BIN% -m black .
if errorlevel 1 exit /b 1
%PYTHON_BIN% -m ruff check . --fix
