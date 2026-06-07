@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo Token V1 - VPS Deployment
echo ========================================
echo.

set KEY=%USERPROFILE%\.ssh\LightsailDefaultKey.pem
set VPS=ubuntu@43.205.116.126
set TOKEN_PATH=/opt/token-v1

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
set "TOKEN_DIR=%SCRIPT_DIR%..\"
set "BOT_DIR=%SCRIPT_DIR%..\..\..\TT Wallet\Wallet V1\"

echo VPS: %VPS%
echo Token Path: %TOKEN_PATH%
echo Local Token Dir: %TOKEN_DIR%
echo.

REM Step 1: Create directory
echo [Step 1/8] Creating directory on VPS...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "sudo mkdir -p %TOKEN_PATH%/deploy && sudo chown -R ubuntu:ubuntu %TOKEN_PATH%"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create directory
    pause
    exit /b 1
)
echo   OK
echo.

REM Step 2: Copy token_automation.py
echo [Step 2/8] Copying token_automation.py...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%TOKEN_DIR%token_automation.py" "%VPS%:%TOKEN_PATH%/"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to copy token_automation.py
    pause
    exit /b 1
)
echo   OK
echo.

REM Step 3: Copy env files
echo [Step 3/8] Copying environment files...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%TOKEN_DIR%.env.GJ114" "%VPS%:%TOKEN_PATH%/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%TOKEN_DIR%.env.PP450" "%VPS%:%TOKEN_PATH%/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%TOKEN_DIR%.env.RR1001" "%VPS%:%TOKEN_PATH%/"
echo   OK
echo.

REM Step 4: Copy deploy scripts
echo [Step 4/8] Copying deploy scripts...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%TOKEN_DIR%deploy\setup.sh" "%VPS%:%TOKEN_PATH%/deploy/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%TOKEN_DIR%deploy\crontab.txt" "%VPS%:%TOKEN_PATH%/deploy/"
echo   OK
echo.

REM Step 5: Run setup
echo [Step 5/8] Running setup on VPS...
echo (This may take 2-3 minutes for Chrome installation)
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "sudo bash %TOKEN_PATH%/deploy/setup.sh"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Setup may have had issues, continuing...
)
echo   OK
echo.

REM Step 6: Set cron
echo [Step 6/8] Setting up cron jobs...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "cat %TOKEN_PATH%/deploy/crontab.txt | sudo crontab -"
echo   OK
echo.

REM Step 7: Test GJ114
echo [Step 7/8] Testing GJ114...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "cd %TOKEN_PATH% && source venv/bin/activate && python3 token_automation.py --account GJ114"
echo   OK
echo.

REM Step 8: Update bot
echo [Step 8/8] Updating Telegram bot...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%BOT_DIR%telegram_bot.py" "%VPS%:~/tt-wallet/Wallet V1/"
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "sudo systemctl restart tt-wallet-bot"
echo   OK
echo.

echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Token V1 is now:
echo   - Installed at: %TOKEN_PATH%
echo   - Cron: Mon-Fri 8:31 AM IST
echo   - Bot: /start for menu
echo.
pause
