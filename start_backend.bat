@echo off
setlocal
cd /d "%~dp0backend"

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python 3.11 or 3.12 is required.
    pause
    exit /b 1
  )
  set "PYTHON=py"
) else (
  set "PYTHON=python"
)

if not exist .venv (
  echo [1/4] Creating virtual environment...
  %PYTHON% -m venv .venv || goto :error
)

call .venv\Scripts\activate || goto :error
echo [2/4] Installing backend packages...
python -m pip install -r requirements.txt || goto :error

if not exist .env copy .env.example .env >nul

echo [3/4] Preparing SQLite database and 12,512 Seoul/Gyeonggi location rows...
python -m app.scripts.init_db || goto :error

echo [4/4] Starting FastAPI at http://localhost:8000
python -m uvicorn app.main:app --reload
goto :eof

:error
echo.
echo [ERROR] Backend startup failed. Review the message above.
pause
exit /b 1
