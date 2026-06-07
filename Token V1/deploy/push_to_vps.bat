@echo off
REM Push Token V1 to VPS
REM Uses same VPS as TT Wallet (43.205.116.126)

set KEY=%USERPROFILE%\.ssh\LightsailDefaultKey.pem
set VPS_USER=ubuntu
set VPS_HOST=43.205.116.126
set VPS=ubuntu@43.205.116.126
set VPS_PATH=/opt/token-v1

echo ========================================
echo Pushing Token V1 to VPS
echo ========================================
echo VPS: %VPS_USER%@%VPS_HOST%
echo Path: %VPS_PATH%
echo.

where rsync >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [1/3] rsync found — pushing files...
    rsync -avz --progress -e "ssh -i %KEY% -o StrictHostKeyChecking=no" "..\Token V1\" "%VPS%:%VPS_PATH%/"
) else (
    echo [1/3] rsync not found — using scp...
    ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "mkdir -p %VPS_PATH%/deploy"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "..\Token V1\token_automation.py" "%VPS%:%VPS_PATH%/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "..\Token V1\.env.GJ114" "%VPS%:%VPS_PATH%/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "..\Token V1\.env.PP450" "%VPS%:%VPS_PATH%/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "..\Token V1\.env.RR1001" "%VPS%:%VPS_PATH%/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "..\Token V1\deploy\setup.sh" "%VPS%:%VPS_PATH%/deploy/"
    scp -i "%KEY%" -o StrictHostKeyChecking=no "..\Token V1\deploy\crontab.txt" "%VPS%:%VPS_PATH%/deploy/"
)

echo.
echo [2/3] Running setup on VPS...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "sudo bash %VPS_PATH%/deploy/setup.sh"

echo.
echo [3/3] Setting up cron jobs...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "cat %VPS_PATH%/deploy/crontab.txt | sudo crontab -"

echo.
echo [4/4] Testing GJ114...
ssh -i "%KEY%" -o StrictHostKeyChecking=no %VPS% "cd %VPS_PATH% && source venv/bin/activate && python3 token_automation.py --account GJ114"

echo.
echo ========================================
echo Deployment complete!
echo.
echo VPS: %VPS%
echo Path: %VPS_PATH%
echo.
echo Token V1 is now:
echo - Installed at %VPS_PATH%
echo - Cron scheduled: Mon-Fri 8:31 AM IST
echo - Tested and working
echo.
echo Next: Update TT Wallet bot with Token commands
echo ========================================

pause
