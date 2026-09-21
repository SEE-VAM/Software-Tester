@echo off
title Installing AutoQA Robot Dependencies...
echo ==================================================================
echo   Installing Python Dependencies for AutoQA Testing Robot
echo ==================================================================
cd /d "%~dp0"

echo [1/2] Installing Python packages from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install python packages. Please check your internet or Python installation.
    pause
    exit /b 1
)

echo.
echo [2/2] Installing Playwright Chromium browser binaries...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [WARNING] Playwright browser download had an issue. Retrying...
    python -m playwright install
)

echo.
echo ==================================================================
echo   [SUCCESS] Setup Completed! You can now run START_TESTER.bat
echo ==================================================================
pause
