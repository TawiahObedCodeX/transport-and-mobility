@echo off
REM ============================================================
REM start.bat — One-click launcher for MOVA (Transport & Mobility AI)
REM
REM This script opens TWO terminal windows:
REM   Terminal 1: Runs the Python Flask backend server (server.py)
REM   Terminal 2: Runs the React frontend dev server (Vite)
REM
REM Just double-click this file to start everything!
REM ============================================================

REM Print a welcome message in the current window
echo ============================================================
echo  Starting MOVA — Transport & Mobility AI Agent
echo ============================================================
echo.
echo  Opening server terminal (Flask backend)...
echo  Opening UI terminal (React frontend)...
echo.
echo  Close both terminal windows to stop MOVA.
echo ============================================================
echo.

REM Start the Flask backend server in a new terminal window
REM start "WINDOW_TITLE" "COMMAND"
start "MOVA Server" cmd /k "echo MOVA Flask Server & echo. & python server.py"

REM Wait 3 seconds so the server has time to start before the frontend loads
timeout /t 3 /nobreak >nul

REM Start the React frontend in another new terminal window
REM The /d flag sets the working directory to mova-ui
start "MOVA UI" cmd /k "echo MOVA React Frontend & echo. & cd /d "%~dp0mova-ui" && npm run dev"

REM Print instructions for the user
echo.
echo  MOVA is starting up...
echo.
echo  Backend:  http://localhost:5000
echo  Frontend: http://localhost:5173
echo.
echo  Press any key to close this launcher window
echo  (the server and UI will keep running in their own windows).
echo.
pause
