@echo off
REM ============================================================
REM start.bat — One-click launcher for MOVA (Transport & Mobility AI)
REM
REM This script opens TWO terminal windows:
REM   Terminal 1: Runs the FastAPI backend server (Uvicorn)
REM   Terminal 2: Runs the React frontend dev server (Vite)
REM
REM Just double-click this file to start everything!
REM ============================================================

REM Print a welcome message in the current window
echo ============================================================
echo  Starting MOVA — Transport & Mobility AI Agent
echo ============================================================
echo.
echo  Opening server terminal (FastAPI backend)...
echo  Opening UI terminal (React frontend)...
echo.
echo  Close both terminal windows to stop MOVA.
echo ============================================================
echo.

REM Start the FastAPI backend server in a new terminal window
start "MOVA Server" cmd /k "echo MOVA FastAPI Server & echo. & cd /d "%~dp0backend" && uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload"

REM Wait 3 seconds so the server has time to start before the frontend loads
timeout /t 3 /nobreak >nul

REM Start the React frontend in another new terminal window
start "MOVA UI" cmd /k "echo MOVA React Frontend & echo. & cd /d "%~dp0mova-ui" && npm run dev"

REM Print instructions for the user
echo.
echo  MOVA is starting up...
echo.
echo  Backend:  http://localhost:5000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:5000/docs
echo.
echo  Press any key to close this launcher window
echo  (the server and UI will keep running in their own windows).
echo.
pause
