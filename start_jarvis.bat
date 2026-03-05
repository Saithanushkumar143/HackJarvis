@echo off
title JARVIS — Desktop AI Assistant
color 0B
cls

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   J.A.R.V.I.S — Desktop AI Assistant                ║
echo  ║   Just A Rather Very Intelligent System              ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║   Starting up...                                     ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found! Install from python.org
    pause
    exit /b 1
)

:: Check .env
if not exist ".env" (
    echo  [SETUP] Creating .env from template...
    copy ".env.example" ".env" >nul
    echo  [ACTION REQUIRED] Please edit .env with your API keys
    notepad .env
    pause
)

:: Install requirements if needed
if not exist "venv" (
    echo  [SETUP] Creating virtual environment...
    python -m venv venv
    echo  [SETUP] Installing requirements...
    call venv\Scripts\activate
    pip install -r requirements.txt --quiet
) else (
    call venv\Scripts\activate
)

cls
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   J.A.R.V.I.S — Choose Mode                         ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║   1. GUI Mode (Open browser UI + Python backend)     ║
echo  ║   2. Voice Only Mode (Terminal only)                 ║
echo  ║   3. Exit                                            ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

set /p choice="  Enter choice (1/2/3): "

if "%choice%"=="1" goto GUI
if "%choice%"=="2" goto VOICE
if "%choice%"=="3" exit /b 0
goto :eof

:GUI
echo.
echo  [GUI] Starting WebSocket backend...
start /b python backend\ws_bridge.py
timeout /t 2 /nobreak >nul
echo  [GUI] Opening JARVIS UI in Chrome...
start chrome --app="file:///%CD%\frontend\jarvis_ui.html"
echo.
echo  [RUNNING] JARVIS GUI is active!
echo  [TIP] Press Ctrl+C in the terminal to stop the backend.
echo.
python backend\ws_bridge.py
goto :eof

:VOICE
echo.
echo  [VOICE] Starting JARVIS in voice-only mode...
echo  [TIP] Say "Jarvis" to wake up. Say "go to sleep" to standby.
echo.
python main.py
goto :eof
