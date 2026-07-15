@echo off
setlocal
cd /d "%~dp0frontend"

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js 20 or later is required.
  pause
  exit /b 1
)

if not exist .env copy .env.example .env >nul
echo [1/2] Installing frontend packages...
call npm install || goto :error
echo [2/2] Starting Vue at http://localhost:5173
call npm run dev
goto :eof

:error
echo.
echo [ERROR] Frontend startup failed. Review the message above.
pause
exit /b 1
