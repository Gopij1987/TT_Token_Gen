# GitHub Secrets Configuration Guide

## Overview
This guide explains how to configure GitHub Secrets for the Stocko Auto Login script to work in CI/CD pipelines.

**Key Principle:** Same naming convention for both local `.env` files and GitHub Secrets - **NO CONFUSION!**

## Local Development (`.env` files)
For local testing, use `.env.<USER_ID>` files with user-friendly naming:
- `.env.GJ114` - GJ114 user credentials
- `.env.PP450` - PP450 user credentials
- etc.

**Format:** Each `.env` file uses `<USER_ID>_*` variables:
```
# .env.GJ114
GJ114_USERNAME=GJ114
GJ114_PASSWORD=***
GJ114_TOTP_SECRET=***
GJ114_AUTH_CODE=2310473
TELEGRAM_BOT_TOKEN=***
TELEGRAM_CHAT_ID=***
```

## GitHub Secret Names
For GitHub Actions, use **EXACTLY THE SAME NAMING** - no conversion needed!

### For User GJ114:
| Secret Name | Value | Local File |
|-------------|-------|------------|
| `GJ114_USERNAME` | GJ114 | .env.GJ114 |
| `GJ114_PASSWORD` | *** | .env.GJ114 |
| `GJ114_TOTP_SECRET` | *** | .env.GJ114 |
| `GJ114_AUTH_CODE` | 2310473 | .env.GJ114 |

### For User PP450:
| Secret Name | Value | Local File |
|-------------|-------|------------|
| `PP450_USERNAME` | PP450 | .env.PP450 |
| `PP450_PASSWORD` | *** | .env.PP450 |
| `PP450_TOTP_SECRET` | *** | .env.PP450 |
| `PP450_AUTH_CODE` | 733517 | .env.PP450 |

### Telegram (Shared across all users):
| Secret Name | Value | Local File |
|-------------|-------|------------|
| `TELEGRAM_BOT_TOKEN` | *** | .env.* (any file) |
| `TELEGRAM_CHAT_ID` | *** | .env.* (any file) |

## How to Add Secrets to GitHub

1. Go to your GitHub repository
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Add each secret one by one:
   - Name: `GJ114_USERNAME`
   - Value: `GJ114`
   - Click **Add secret**

5. Repeat for all secrets in the tables above

## GitHub Actions Workflow Example

```yaml
name: Stocko Auto Login - User Selection

on:
  workflow_dispatch:
    inputs:
      user:
        description: 'Which user to login'
        required: true
        type: choice
        options:
          - GJ114
          - PP450

jobs:
  auto-login:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run Auto Login
        env:
          USER_ID: ${{ github.event.inputs.user }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          GJ114_USERNAME: ${{ secrets.GJ114_USERNAME }}
          GJ114_PASSWORD: ${{ secrets.GJ114_PASSWORD }}
          GJ114_TOTP_SECRET: ${{ secrets.GJ114_TOTP_SECRET }}
          GJ114_AUTH_CODE: ${{ secrets.GJ114_AUTH_CODE }}
          PP450_USERNAME: ${{ secrets.PP450_USERNAME }}
          PP450_PASSWORD: ${{ secrets.PP450_PASSWORD }}
          PP450_TOTP_SECRET: ${{ secrets.PP450_TOTP_SECRET }}
          PP450_AUTH_CODE: ${{ secrets.PP450_AUTH_CODE }}
        run: |
          cd essential
          python stocko_auto_login_GJ114_API_V2.py
```

## Script Behavior

When you run the script:

### Local Development
```bash
python stocko_auto_login_GJ114_API_V2.py
# Loads: .env.GJ114 → STOCKO_* variables
```

### GitHub Actions (with USER_ID env var)
```bash
export USER_ID=GJ114
python stocko_auto_login_GJ114_API_V2.py
# Loads: GJ114_* environment secrets
```

### Manual Override (if needed)
```bash
export USER_ID=PP450
python stocko_auto_login_GJ114_API_V2.py
# Loads: .env.PP450 OR PP450_* secrets
```

## Adding a New User

1. **Local:** Create `.env.NEWUSER` with:
   ```
   STOCKO_USERNAME=NEWUSER
   STOCKO_PASSWORD=***
   STOCKO_TOTP_SECRET=***
   STOCKO_AUTH_CODE=2310473
   TELEGRAM_BOT_TOKEN=*** (same as others)
   TELEGRAM_CHAT_ID=*** (same as others)
   ```

2. **GitHub:** Add 4 new secrets:
   - `NEWUSER_USERNAME`
   - `NEWUSER_PASSWORD`
   - `NEWUSER_TOTP_SECRET`
   - `NEWUSER_AUTH_CODE`

3. **Workflow:** Update GitHub Actions workflow to include them:
   ```yaml
   NEWUSER_USERNAME: ${{ secrets.NEWUSER_USERNAME }}
   NEWUSER_PASSWORD: ${{ secrets.NEWUSER_PASSWORD }}
   NEWUSER_TOTP_SECRET: ${{ secrets.NEWUSER_TOTP_SECRET }}
   NEWUSER_AUTH_CODE: ${{ secrets.NEWUSER_AUTH_CODE }}
   ```

## Security Best Practices

✅ **DO:**
- Store credentials in GitHub Secrets, never in code
- Use different TOTP secrets per user
- Rotate passwords regularly
- Use the same Telegram bot token for all users
- Keep `.env.*` files in `.gitignore`

❌ **DON'T:**
- Commit `.env` files to git
- Hardcode credentials in scripts
- Share secrets in messages or logs
- Mix user credentials

## Troubleshooting

### "AUTH_CODE not set"
- Check `.env.GJ114` exists in `essential/` folder
- Or set GitHub Secrets correctly
- Or run with: `export USER_ID=GJ114` before running

### Wrong user logging in
- Verify `USER_ID` environment variable
- Check which `.env` file is being loaded
- Confirm GitHub Secrets have correct USER_ID prefix

### Telegram notification not sent
- Verify `TELEGRAM_BOT_TOKEN` is set
- Verify `TELEGRAM_CHAT_ID` is set
- Check bot is still valid (not revoked)
