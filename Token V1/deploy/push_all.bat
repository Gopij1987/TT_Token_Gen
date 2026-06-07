@echo off
echo ========================================
echo Pushing ALL Files to VPS
echo ========================================
echo.

set KEY=%USERPROFILE%\.ssh\LightsailDefaultKey.pem
set VPS=ubuntu@43.205.116.126
set TOKEN_PATH=/opt/token-v1
set BOT_PATH=~/tt-wallet/Wallet V1

REM Get correct local paths
set "LOCAL_TOKEN=C:\Users\gopij\OneDrive\Synced\Python\Auto Login\Token V1"
set "LOCAL_BOT=C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\Wallet V1"

echo KEY: %KEY%
echo VPS: %VPS%
echo.

REM Step 1: Push Token V1 files
echo [1/5] Pushing Token V1 files...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_TOKEN%\token_automation.py" "%VPS%:%TOKEN_PATH%/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_TOKEN%\.env.GJ114" "%VPS%:%TOKEN_PATH%/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_TOKEN%\.env.PP450" "%VPS%:%TOKEN_PATH%/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_TOKEN%\.env.RR1001" "%VPS%:%TOKEN_PATH%/"
echo   OK
echo.

REM Step 2: Push deploy scripts
echo [2/5] Pushing deploy scripts...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_TOKEN%\deploy\setup.sh" "%VPS%:%TOKEN_PATH%/deploy/"
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_TOKEN%\deploy\crontab.txt" "%VPS%:%TOKEN_PATH%/deploy/"
echo   OK
echo.

REM Step 3: Push updated bot (with correct path)
echo [3/5] Pushing updated telegram_bot.py...
scp -i "%KEY%" -o StrictHostKeyChecking=no "%LOCAL_BOT%\telegram_bot.py" "%VPS%:%BOT_PATH%/"
echo   OK
echo.

REM Step 4: Restart bot
echo [4/5] Restarting bot service...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "sudo systemctl restart tt-wallet-bot"
echo   OK
echo.

REM Step 5: Verify
echo [5/5] Verifying files...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "ls -la %TOKEN_PATH%/ && echo '---' && grep 'complete' ~/tt-wallet/Wallet\ V1/telegram_bot.py | head -1"
echo   OK
echo.

echo ========================================
echo ALL FILES PUSHED!
echo ========================================
echo.
echo Token V1: %TOKEN_PATH%
echo Bot: %BOT_PATH%
echo.
echo Test with: /start -^> Token -^> GJ114
echo.

pause
