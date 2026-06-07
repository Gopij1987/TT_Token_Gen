@echo off
echo ========================================
echo SSH Connection Test
echo ========================================
echo.
echo Testing SSH connection to VPS...
echo VPS: ubuntu@43.205.116.126
echo Key: %USERPROFILE%\.ssh\LightsailDefaultKey.pem
echo.

ssh -i "%USERPROFILE%\.ssh\LightsailDefaultKey.pem" -o StrictHostKeyChecking=no ubuntu@43.205.116.126 "echo Connection successful! Server: $(uname -a)"

if %ERRORLEVEL% == 0 (
    echo.
    echo ========================================
    echo SSH Connection: SUCCESS
echo ========================================
    echo.
    echo Next step: Run deploy.bat
) else (
    echo.
    echo ========================================
    echo SSH Connection: FAILED
echo ========================================
    echo.
    echo Possible issues:
    echo 1. VPS IP may have changed
    echo 2. SSH key permissions issue
    echo 3. VPS is not running
    echo.
    echo Check: ssh -i key.pem ubuntu@43.205.116.126
)

pause
