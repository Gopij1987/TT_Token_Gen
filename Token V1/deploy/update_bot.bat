@echo off
REM Update TT Wallet bot on VPS with Token V1 commands
REM Uses same VPS as TT Wallet (43.205.116.126)

set KEY=%USERPROFILE%\.ssh\LightsailDefaultKey.pem
set VPS=ubuntu@43.205.116.126
set BOT_PATH=~/tt-wallet/Wallet V1

echo ========================================
echo Updating TT Wallet Bot with Token V1
echo ========================================
echo VPS: %VPS%
echo Bot Path: %BOT_PATH%
echo.

echo [1/2] Pushing extended telegram_bot.py...
scp -i "%KEY%" -o StrictHostKeyChecking=no "..\..\TT Wallet\Wallet V1\telegram_bot.py" "%VPS%:%BOT_PATH%/"

echo.
echo [2/2] Restarting bot service...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "sudo systemctl restart tt-wallet-bot"

echo.
echo ========================================
echo Bot updated and restarted!
echo.
echo New commands available:
echo   /start - Main menu (Wallet/Token/Status)
echo   /runtoken - Token account selection
echo   🔑 Token button - Account menu
echo.
echo Test: Send /start to your bot
echo ========================================

pause
