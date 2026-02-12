# GitHub Automation Setup Guide - PP450

## Overview
This guide explains how to automate the Stocko login script to run daily at 8:25 AM using GitHub Actions.

## Prerequisites
1. A GitHub account
2. This repository pushed to GitHub
3. Your Stocko credentials
4. Your TOTP secret key

---

## Step 1: Get Your TOTP Secret

### What is TOTP Secret?
The TOTP secret is a BASE32-encoded key used to generate 2FA codes. You need this one-time secret (not the 6-digit codes).

### How to Get It:

**Option A: From QR Code (When Setting Up 2FA)**
1. When Stocko shows you the QR code for 2FA setup
2. Look for a "Can't scan?" or "Manual entry" option
3. Copy the SECRET KEY (looks like: `JBSWY3DPEHPK3PXP`)

**Option B: From Existing Authenticator App**
- **Google Authenticator**: Cannot export secrets (need to reset 2FA)
- **Authy**: Cannot export easily (need to reset 2FA)
- **Microsoft Authenticator**: Go to account → Settings → Show secret
- **1Password/Bitwarden**: View item → Show TOTP secret

**Option C: Reset 2FA on Stocko**
1. Disable 2FA in Stocko settings
2. Re-enable 2FA
3. When shown the QR code, click "Manual entry"
4. Copy the secret key
5. Complete setup with your authenticator app

---

## Step 2: Set Up GitHub Repository

### 2.1 Create GitHub Repository
```bash
cd "c:\Users\gopij\OneDrive\Synced\Python\Auto Login"
git init
git add .
git commit -m "Initial commit - PP450 Auto Login"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/stocko-auto-login-pp450.git
git push -u origin main
```

### 2.2 Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `STOCKO_USERNAME` | Your Stocko username/email | gopij@example.com |
| `STOCKO_PASSWORD` | Your Stocko password | YourPassword123! |
| `STOCKO_TOTP_SECRET` | Your TOTP secret key | JBSWY3DPEHPK3PXP |
| `STOCKO_AUTH_CODE` | Auth code from URL | 733517 |

**Important:** 
- Secrets are encrypted and cannot be viewed after creation
- Never commit secrets to your repository
- Each secret must be added separately

---

## Step 3: Verify Workflow Setup

### 3.1 Check Workflow File
The workflow file is located at: `.github/workflows/auto_login_PP450.yml`

It's configured to run at **8:25 AM IST (2:55 AM UTC)** daily.

### 3.2 Test Manual Run
1. Go to GitHub repository
2. Click **Actions** tab
3. Select **Stocko Auto Login - PP450** workflow
4. Click **Run workflow** → **Run workflow**
5. Monitor the execution

---

## Step 4: Monitor & Verify

### Check Workflow Runs
1. Go to **Actions** tab in your repository
2. View recent workflow runs
3. Click on a run to see detailed logs

### Download Tokens (if generated)
1. Open a successful workflow run
2. Scroll to **Artifacts** section
3. Download `stocko-tokens-pp450`

---

## Environment Variables Reference

The script uses these environment variables in automated mode:

```bash
# Required for automation
STOCKO_AUTO_MODE=true         # Enables automated mode
STOCKO_USERNAME=your_username  # Your login username
STOCKO_PASSWORD=your_password  # Your login password
STOCKO_TOTP_SECRET=your_secret # TOTP secret key (BASE32)
STOCKO_AUTH_CODE=733517        # Auth code from URL
```

---

## Testing Locally (Optional)

Before pushing to GitHub, test locally:

```powershell
# Set environment variables (PowerShell)
$env:STOCKO_AUTO_MODE="true"
$env:STOCKO_USERNAME="your_username"
$env:STOCKO_PASSWORD="your_password"
$env:STOCKO_TOTP_SECRET="JBSWY3DPEHPK3PXP"
$env:STOCKO_AUTH_CODE="733517"

# Run script
python stocko_auto_login_PP450.py
```

---

## Schedule Reference

The workflow runs at **8:25 AM IST** every day.

**Cron Expression:** `55 2 * * *` (2:55 AM UTC = 8:25 AM IST)

### Change Schedule:
Edit `.github/workflows/auto_login_PP450.yml`:
```yaml
schedule:
  - cron: 'MINUTE HOUR * * *'  # Format: minute hour day month weekday
```

**Common schedules:**
- 8:25 AM IST: `55 2 * * *`
- 9:00 AM IST: `30 3 * * *`
- Every 6 hours: `0 */6 * * *`

---

## Troubleshooting

### Workflow not running?
- Check if Actions are enabled: Settings → Actions → General
- Verify workflow file syntax
- Check repository permissions

### Login failing?
- Verify all secrets are set correctly
- Check if TOTP secret is valid
- Review workflow logs for error messages

### TOTP code invalid?
- Ensure TOTP_SECRET is the BASE32 secret, not a 6-digit code
- Time sync issues: GitHub servers use UTC
- Try regenerating TOTP secret

### How to view logs?
1. Go to Actions tab
2. Click on workflow run
3. Click on job name
4. Expand steps to view detailed logs

---

## Security Notes

✅ **Do:**
- Use GitHub Secrets for all sensitive data
- Keep your repository private
- Rotate credentials periodically
- Review workflow logs carefully

❌ **Don't:**
- Commit credentials to repository
- Share your TOTP secret
- Make secrets public
- Store passwords in code

---

## Support

- Tag: **PP450**
- Workflow: `auto_login_PP450.yml`
- Script: `stocko_auto_login_PP450.py`

For issues, check workflow logs in the Actions tab.
