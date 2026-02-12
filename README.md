# Stocko Auto Login - GJ114

Production-ready auto-login script for Stocko Broker with Telegram notifications.

## Quick Start

### Local Development

1. **Create `.env.GJ114` file** (use `.env.example` as template):
```bash
cp essential/.env.example essential/.env.GJ114
```

2. **Fill in credentials** in `.env.GJ114`:
```
GJ114_USERNAME=your_username
GJ114_PASSWORD=your_password
GJ114_TOTP_SECRET=your_totp_secret
GJ114_AUTH_CODE=2310473
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

3. **Run the script**:
```bash
python essential/stocko_auto_login_GJ114_API_V2.py
```

**Result:** ~3.4 seconds login with Telegram notification ✅

---

## GitHub Security

### ✅ What's Protected

- ✅ `.env*` files are in `.gitignore` - **NEVER pushed to GitHub**
- ✅ Only `.env.example` (template) is committed
- ✅ Credentials stay local + GitHub Secrets only

### ❌ What's NOT Protected (Don't Do)

```python
# ❌ NEVER hardcode credentials
username = "GJ114"
password = "Gopi@2026"
```

```bash
# ❌ NEVER pass credentials as command line args
python script.py --password=secret
```

### ✅ What You Should Do

**For GitHub Actions CI/CD:**

1. Go to **Settings → Secrets and variables → Actions**
2. Add these secrets:
   - `GJ114_USERNAME`
   - `GJ114_PASSWORD`
   - `GJ114_TOTP_SECRET`
   - `GJ114_AUTH_CODE`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

3. Use in workflow:
```yaml
name: Auto Login
on: [workflow_dispatch]
jobs:
  login:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python essential/stocko_auto_login_GJ114_API_V2.py
        env:
          GJ114_USERNAME: ${{ secrets.GJ114_USERNAME }}
          GJ114_PASSWORD: ${{ secrets.GJ114_PASSWORD }}
          GJ114_TOTP_SECRET: ${{ secrets.GJ114_TOTP_SECRET }}
          GJ114_AUTH_CODE: ${{ secrets.GJ114_AUTH_CODE }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

---

## Files

| File | Purpose | Committed? |
|------|---------|-----------|
| `.env.GJ114` | **Local credentials** | ❌ **NO** (in .gitignore) |
| `.env.example` | Template | ✅ YES (example only) |
| `stocko_auto_login_GJ114_API_V2.py` | Production script | ✅ YES |
| `requirements_gj114.txt` | Dependencies | ✅ YES |
| `.gitignore` | Security rules | ✅ YES |

---

## Features

✅ **Fast:** 3.4 seconds per login (API-based, no browser)  
✅ **Reliable:** TOTP retry logic, response validation  
✅ **Observable:** Telegram notifications on success/failure  
✅ **Scalable:** Easy to add more users via new `.env` files  
✅ **Secure:** Credentials protected, never in logs  

---

## Environment Variables

### Local (.env.GJ114)
```
GJ114_USERNAME=GJ114
GJ114_PASSWORD=***
GJ114_TOTP_SECRET=***
GJ114_AUTH_CODE=2310473
TELEGRAM_BOT_TOKEN=***
TELEGRAM_CHAT_ID=***
```

### GitHub Secrets
Same names as above, configured in Settings → Secrets

---

## Troubleshooting

### "AUTH_CODE not set"
→ Check `.env.GJ114` exists and has `GJ114_AUTH_CODE`

### "No form found"
→ Server might be down or response changed. Check logs.

### Telegram notification not sent
→ Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct

### Accidental .env commit?
```bash
# Remove from git (but keep locally)
git rm --cached .env.GJ114
git commit -m "Remove .env.GJ114 from git history"

# Rotate passwords immediately!
```

---

## License

Private - Do not share credentials or code publicly
