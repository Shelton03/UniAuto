@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "RESEARCH_OS_PYTHON=.venv\Scripts\python.exe"
) else if exist "uni_venv\Scripts\python.exe" (
  set "RESEARCH_OS_PYTHON=uni_venv\Scripts\python.exe"
) else (
  echo Virtual environment not found. Create it with: py -m venv .venv
  exit /b 1
)
"%RESEARCH_OS_PYTHON%" automation\weekly_update.py
endlocal
