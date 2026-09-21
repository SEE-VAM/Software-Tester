@echo off
title AutoQA Robot - Automated POS Testing Engine
cd /d "%~dp0"

echo ==================================================================
echo   🤖 AutoQA Robot - Automated POS Testing Engine
echo   Targeting Retail POS (e.g. BrainShop) & Web Applications
echo ==================================================================
echo.

:: Check if flask or playwright is available
python -c "import flask, playwright" >nul 2>&1
if %errorlevel% neq 0 (
    echo [NOTICE] First-time setup detected. Installing dependencies...
    call install_requirements.bat
)

echo Starting Telemetry & Testing Server on Port 9090...
start "" http://localhost:9090

python server.py
pause
