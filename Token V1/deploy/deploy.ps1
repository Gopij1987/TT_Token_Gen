# Token V1 - VPS Deployment Script
# Run in PowerShell as Administrator

$ErrorActionPreference = "Stop"

$KEY = "C:\Users\gopij\.ssh\LightsailDefaultKey.pem"
$VPS = "ubuntu@43.205.116.126"
$TOKEN_PATH = "/opt/token-v1"
$LOCAL_TOKEN = "C:\Users\gopij\OneDrive\Synced\Python\Auto Login\Token V1"
$LOCAL_BOT = "C:\Users\gopij\OneDrive\Synced\Python\TT Wallet\Wallet V1"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Token V1 - VPS Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "VPS: $VPS" -ForegroundColor Yellow
Write-Host "Token Path: $TOKEN_PATH" -ForegroundColor Yellow
Write-Host ""

# Step 1: Create directory on VPS
Write-Host "[Step 1/8] Creating directory on VPS..." -ForegroundColor Green
ssh -i $KEY -o StrictHostKeyChecking=no $VPS "sudo mkdir -p $TOKEN_PATH/deploy && sudo chown -R ubuntu:ubuntu $TOKEN_PATH"
Write-Host "  ✓ Directory created" -ForegroundColor Green

# Step 2: Copy token_automation.py
Write-Host "[Step 2/8] Copying token_automation.py..." -ForegroundColor Green
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_TOKEN\token_automation.py" "$VPS`:$TOKEN_PATH/"
Write-Host "  ✓ token_automation.py copied" -ForegroundColor Green

# Step 3: Copy environment files
Write-Host "[Step 3/8] Copying environment files..." -ForegroundColor Green
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_TOKEN\.env.GJ114" "$VPS`:$TOKEN_PATH/"
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_TOKEN\.env.PP450" "$VPS`:$TOKEN_PATH/"
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_TOKEN\.env.RR1001" "$VPS`:$TOKEN_PATH/"
Write-Host "  ✓ All .env files copied" -ForegroundColor Green

# Step 4: Copy deploy scripts
Write-Host "[Step 4/8] Copying deploy scripts..." -ForegroundColor Green
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_TOKEN\deploy\setup.sh" "$VPS`:$TOKEN_PATH/deploy/"
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_TOKEN\deploy\crontab.txt" "$VPS`:$TOKEN_PATH/deploy/"
Write-Host "  ✓ Deploy scripts copied" -ForegroundColor Green

# Step 5: Run setup
Write-Host "[Step 5/8] Running setup script on VPS..." -ForegroundColor Green
Write-Host "  (This may take 2-3 minutes for Chrome installation)" -ForegroundColor Yellow
ssh -i $KEY -o StrictHostKeyChecking=no $VPS "sudo bash $TOKEN_PATH/deploy/setup.sh"
Write-Host "  ✓ Setup complete" -ForegroundColor Green

# Step 6: Set cron jobs
Write-Host "[Step 6/8] Setting up cron jobs..." -ForegroundColor Green
ssh -i $KEY -o StrictHostKeyChecking=no $VPS "cat $TOKEN_PATH/deploy/crontab.txt | sudo crontab -"
Write-Host "  ✓ Cron jobs set (Mon-Fri 8:31 AM IST)" -ForegroundColor Green

# Step 7: Test GJ114
Write-Host "[Step 7/8] Testing GJ114 login..." -ForegroundColor Green
ssh -i $KEY -o StrictHostKeyChecking=no $VPS "cd $TOKEN_PATH && source venv/bin/activate && python3 token_automation.py --account GJ114"
Write-Host "  ✓ GJ114 test complete" -ForegroundColor Green

# Step 8: Update bot
Write-Host "[Step 8/8] Updating Telegram bot..." -ForegroundColor Green
scp -i $KEY -o StrictHostKeyChecking=no "$LOCAL_BOT\telegram_bot.py" "$VPS`:~/tt-wallet/Wallet V1/"
ssh -i $KEY -o StrictHostKeyChecking=no $VPS "sudo systemctl restart tt-wallet-bot"
Write-Host "  ✓ Bot updated and restarted" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Token V1 is now:" -ForegroundColor White
Write-Host "  - Installed at: $TOKEN_PATH" -ForegroundColor White
Write-Host "  - Cron scheduled: Mon-Fri 8:31 AM IST" -ForegroundColor White
Write-Host "  - Bot commands: /start for menu" -ForegroundColor White
Write-Host ""
Write-Host "Test commands:" -ForegroundColor Yellow
Write-Host "  ssh -i $KEY $VPS 'sudo crontab -l'" -ForegroundColor Gray
Write-Host "  ssh -i $KEY $VPS 'tail -f /var/log/token-v1/*.log'" -ForegroundColor Gray
Write-Host ""
