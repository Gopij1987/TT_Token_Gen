# PP450 - Step-by-Step Action Plan

## STEP 1: Get Your TOTP Secret ⏰ (5-10 minutes)

### Option A: If setting up 2FA for first time
1. Go to Stocko → Settings → Security
2. Click "Enable Two-Factor Authentication"
3. When QR code appears, click "Can't scan?" or "Manual entry"
4. **COPY THE SECRET KEY** (looks like: JBSWY3DPEHPK3PXP)
5. Save it somewhere safe temporarily
6. Scan QR code with your authenticator app
7. Complete 2FA setup

### Option B: If you already have 2FA enabled
**You'll need to reset it to get the secret:**
1. Go to Stocko → Settings → Security
2. Disable Two-Factor Authentication
3. Re-enable Two-Factor Authentication
4. Follow Option A steps above

### What you need:
- [ ] TOTP Secret Key (BASE32 format)

---

## STEP 2: Install Dependencies Locally 💻 (2 minutes)

Open PowerShell in this folder and run:

```powershell
pip install -r requirements_PP450.txt
```

---

## STEP 3: Test Script Locally 🧪 (5 minutes)

### Manual Mode Test:
```powershell
python stocko_auto_login_PP450.py
```

Follow prompts to enter:
- Auth code (press Enter for default: 733517)
- Username
- Password  
- TOTP code from your app

**Expected result:** "Authentication complete!"

### Automated Mode Test:
```powershell
$env:STOCKO_AUTO_MODE="true"
$env:STOCKO_USERNAME="YOUR_USERNAME"
$env:STOCKO_PASSWORD="YOUR_PASSWORD"
$env:STOCKO_TOTP_SECRET="YOUR_TOTP_SECRET"
$env:STOCKO_AUTH_CODE="733517"

python stocko_auto_login_PP450.py
```

**Expected result:** Script runs without prompts and completes automatically

✅ **Checkpoint:** Script works locally before proceeding to GitHub

---

## STEP 4: Create GitHub Repository 🌐 (5 minutes)

### 4.1 Initialize Git (if not done)
```powershell
cd "c:\Users\gopij\OneDrive\Synced\Python\Auto Login"
git init
git add .
git commit -m "Initial commit - PP450 Auto Login"
```

### 4.2 Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `stocko-auto-login-pp450`
3. Set to **Private** (IMPORTANT!)
4. Don't initialize with README (we already have files)
5. Click "Create repository"

### 4.3 Push Code to GitHub
```powershell
git remote add origin https://github.com/YOUR_USERNAME/stocko-auto-login-pp450.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username

---

## STEP 5: Configure GitHub Secrets 🔐 (5 minutes)

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. Left sidebar: **Secrets and variables** → **Actions**
4. Click **New repository secret** button

Add these 4 secrets ONE BY ONE:

### Secret 1:
- Name: `STOCKO_USERNAME`
- Value: `your_stocko_username_or_email`
- Click "Add secret"

### Secret 2:
- Name: `STOCKO_PASSWORD`
- Value: `your_stocko_password`
- Click "Add secret"

### Secret 3:
- Name: `STOCKO_TOTP_SECRET`
- Value: `YOUR_TOTP_SECRET_FROM_STEP1`
- Click "Add secret"

### Secret 4:
- Name: `STOCKO_AUTH_CODE`
- Value: `733517`
- Click "Add secret"

**Verify:** You should see 4 secrets listed (values are hidden)

---

## STEP 6: Enable GitHub Actions ⚙️ (2 minutes)

1. In your repository, click **Settings**
2. Left sidebar: **Actions** → **General**
3. Under "Actions permissions":
   - Select "Allow all actions and reusable workflows"
4. Click **Save**

---

## STEP 7: Test Workflow Manually 🚀 (5 minutes)

1. Go to **Actions** tab (top menu)
2. Left sidebar: Click "Stocko Auto Login - PP450"
3. Right side: Click **Run workflow** dropdown
4. Click green **Run workflow** button
5. Wait 10-20 seconds, then refresh page
6. Click on the workflow run to see details
7. Click on the job name to see logs

**Expected result:**
- ✅ Green checkmark = Success
- ❌ Red X = Check logs for errors

### If successful:
- Scroll down to **Artifacts** section
- Download `stocko-tokens-pp450` (if tokens were generated)

---

## STEP 8: Verify Schedule ⏰ (1 minute)

The workflow is now set to run automatically at **8:25 AM IST** every day.

Check `.github/workflows/auto_login_PP450.yml`:
```yaml
schedule:
  - cron: '55 2 * * *'  # 8:25 AM IST
```

**Next automatic run:** Tomorrow at 8:25 AM IST

You can view runs in the **Actions** tab.

---

## STEP 9: Monitor & Verify 📊 (Ongoing)

### Daily Monitoring:
1. Go to **Actions** tab
2. Check if today's run succeeded (green ✅)
3. Click on run to see logs if needed

### Download Tokens:
1. Open successful workflow run
2. Scroll to **Artifacts**
3. Download `stocko-tokens-pp450`

---

## Quick Checklist ✅

- [ ] Got TOTP secret from Stocko
- [ ] Installed dependencies (`pip install -r requirements_PP450.txt`)
- [ ] Tested script locally (manual mode)
- [ ] Tested script locally (auto mode)
- [ ] Created GitHub repository (private)
- [ ] Pushed code to GitHub
- [ ] Added 4 GitHub secrets
- [ ] Enabled GitHub Actions
- [ ] Ran workflow manually and succeeded
- [ ] Verified schedule is set for 8:25 AM IST

---

## Troubleshooting 🔧

### Error: "Credentials not found in environment"
→ Check that all 4 secrets are added in GitHub Settings → Secrets

### Error: "TOTP code invalid"
→ Verify TOTP_SECRET is the BASE32 secret (not 6-digit code)
→ Format: `JBSWY3DPEHPK3PXP` (no spaces)

### Error: "Login failed"
→ Test credentials locally first
→ Check if Stocko website structure changed

### Workflow not running at 8:25 AM
→ Check Actions are enabled in Settings
→ Verify cron expression: `55 2 * * *`
→ GitHub Actions may have 5-10 min delay

### Where are the logs?
→ Actions tab → Click workflow run → Click job name → Expand steps

---

## Support

- **Tag:** PP450
- **Files to check:**
  - Script: `stocko_auto_login_PP450.py`
  - Workflow: `.github/workflows/auto_login_PP450.yml`
  - This guide: `STEP_BY_STEP_PP450.md`

**Need help?** Check logs in Actions tab for detailed error messages.
