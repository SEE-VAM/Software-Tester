@echo off
title Push AutoQA Robot to GitHub
color 0b
echo ========================================================
echo   Pushing AutoQA Robot Project to GitHub
echo   Repository: https://github.com/SEE-VAM/Software-Tester.git
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Git Repository...
if not exist ".git" (
    echo Initializing new Git repository...
    git init
    git branch -M main
)

echo.
echo [2/4] Staging and Committing Changes...
git add -A
git commit -m "feat: AutoQA Robot - Autonomous Software Testing & UI Crawler Engine" >nul 2>nul
echo Done.

echo.
echo [3/4] Configuring Remote Origin...
git remote remove origin >nul 2>nul
git remote add origin https://github.com/SEE-VAM/Software-Tester.git
git remote -v

echo.
echo [4/4] Pushing to GitHub (main branch)...
echo (Make sure you have created the empty repo 'Software-Tester' on github.com/SEE-VAM)
echo.
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Code successfully pushed to GitHub!
    echo   View online: https://github.com/SEE-VAM/Software-Tester
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   [NOTICE] If repository does not exist yet on GitHub:
    echo   1. Open: https://github.com/new
    echo   2. Repository Name: Software-Tester
    echo   3. Click 'Create repository'
    echo   4. Run this script again!
    echo ========================================================
)

echo.
pause
