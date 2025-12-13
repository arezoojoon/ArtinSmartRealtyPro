@echo off
REM ============================================
REM Quick Deploy Script - Windows PowerShell
REM ============================================

echo.
echo ============================================
echo   ArtinSmartRealty - Deploy Button Fix
echo ============================================
echo.

REM Step 1: Check if we have changes to commit
echo [1/5] Checking for local changes...
git status

REM Step 2: Commit new files
echo.
echo [2/5] Committing deployment scripts...
git add .env DEPLOY_BUTTON_FIX_FA.md deploy_button_fix.sh
git commit -m "Add: Deploy scripts and Gemini API config guide" 2>nul
if errorlevel 1 (
    echo No new changes to commit
) else (
    echo Committed successfully
)

REM Step 3: Push to GitHub
echo.
echo [3/5] Pushing to GitHub...
git push origin main

REM Step 4: SSH to server and deploy
echo.
echo [4/5] Connecting to production server...
echo.
echo Please run these commands manually on the server:
echo.
echo ssh root@88.99.45.159
echo cd /opt/ArtinSmartRealtyPro
echo git pull origin main
echo nano .env    # Update GEMINI_API_KEY with real key
echo docker-compose up -d --build backend
echo.

REM Step 5: Instructions
echo.
echo [5/5] Next steps:
echo.
echo 1. Get Gemini API Key from: https://aistudio.google.com/app/apikey
echo 2. SSH to server and update .env
echo 3. Rebuild backend container
echo 4. Test bot in Telegram
echo.
echo ============================================
echo   See DEPLOY_BUTTON_FIX_FA.md for details
echo ============================================
echo.

pause
