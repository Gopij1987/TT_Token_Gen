# GitHub Secrets Setup Guide

This guide shows all GitHub Secrets required for the Stocko auto-login workflows.

## How to Add Secrets

1. Go to GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add each secret from the table below
4. Click **Add secret**

---

## GJ114 User Secrets

| Secret Name | Value | Source |
|-------------|-------|--------|
| `GJ114_USERNAME` | GJ114 | From `.env.GJ114` |
| `GJ114_PASSWORD` | `Gopi@2026` | From `.env.GJ114` |
| `GJ114_TOTP_SECRET` | `V4GG6ERBXLVAUSLH` | From `.env.GJ114` |
| `GJ114_AUTH_CODE` | `2310473` | From `.env.GJ114` |

**Schedule:** Daily at **1:03 UTC**  
**Workflow:** `.github/workflows/stocko-gj114-schedule.yml`

---

## PP450 User Secrets

| Secret Name | Value | Source |
|-------------|-------|--------|
| `PP450_USERNAME` | PP450 | From `.env.PP450` |
| `PP450_PASSWORD` | `Ril@2025` | From `.env.PP450` |
| `PP450_TOTP_SECRET` | `3USTV6L47PZMMJBX` | From `.env.PP450` |
| `PP450_AUTH_CODE` | `733517` | From `.env.PP450` |

**Schedule:** Daily at **2:15 UTC**  
**Workflow:** `.github/workflows/stocko-pp450-schedule.yml`

---

## RR1001 User Secrets

| Secret Name | Value | Source |
|-------------|-------|--------|
| `RR1001_USERNAME` | Your username | From `.env.RR1001` |
| `RR1001_PASSWORD` | Your password | From `.env.RR1001` |
| `RR1001_TOTP_SECRET` | Your TOTP secret | From `.env.RR1001` |
| `RR1001_AUTH_CODE` | Your auth code | From `.env.RR1001` |

**Schedule:** Daily at **3:30 UTC**  
**Workflow:** `.github/workflows/stocko-rr1001-schedule.yml`

---

## Telegram Secrets (Shared by All Users)

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | `8266072198:AAE0xsh0GGiuhX3wmmqmF9MCkSjLUk5ZEq4` |
| `TELEGRAM_CHAT_ID` | `7241656297` |

These are **shared** across all workflows.

---

## Total Secrets Required

- **4 secrets** per user (USERNAME, PASSWORD, TOTP_SECRET, AUTH_CODE)
- **2 secrets** shared (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

For 3 users: **4 × 3 + 2 = 14 total secrets**

---

## Adding Secrets via GitHub CLI (Optional)

```bash
# GJ114
gh secret set GJ114_USERNAME --body "GJ114"
gh secret set GJ114_PASSWORD --body "Gopi@2026"
gh secret set GJ114_TOTP_SECRET --body "V4GG6ERBXLVAUSLH"
gh secret set GJ114_AUTH_CODE --body "2310473"

# PP450
gh secret set PP450_USERNAME --body "PP450"
gh secret set PP450_PASSWORD --body "Ril@2025"
gh secret set PP450_TOTP_SECRET --body "3USTV6L47PZMMJBX"
gh secret set PP450_AUTH_CODE --body "733517"

# RR1001
gh secret set RR1001_USERNAME --body "YOUR_USERNAME"
gh secret set RR1001_PASSWORD --body "YOUR_PASSWORD"
gh secret set RR1001_TOTP_SECRET --body "YOUR_TOTP_SECRET"
gh secret set RR1001_AUTH_CODE --body "YOUR_AUTH_CODE"

# Telegram (shared)
gh secret set TELEGRAM_BOT_TOKEN --body "8266072198:AAE0xsh0GGiuhX3wmmqmF9MCkSjLUk5ZEq4"
gh secret set TELEGRAM_CHAT_ID --body "7241656297"
```

---

## Verify Secrets

```bash
gh secret list
```

---

## Local Development

For local testing, use the `.env.<USERNAME>` files:
- `.env.GJ114` ← GJ114 credentials
- `.env.PP450` ← PP450 credentials
- `.env.RR1001` ← RR1001 credentials

These files are protected by `.gitignore` and **never pushed to GitHub**.

---

## Workflow Schedules

| User | Time (UTC) | Time (IST) | Schedule |
|------|-----------|-----------|----------|
| GJ114 | 1:03 UTC | 6:33 AM | Daily |
| PP450 | 2:15 UTC | 7:45 AM | Daily |
| RR1001 | 3:30 UTC | 9:00 AM | Daily |

---

## View Workflow Runs

**GitHub UI:**
1. Go to **Actions** tab
2. Select the workflow you want to check
3. View past runs and logs

**View all schedules:**
- GJ114: https://github.com/Gopij1987/TT_Token_Gen/actions/workflows/stocko-gj114-schedule.yml
- PP450: https://github.com/Gopij1987/TT_Token_Gen/actions/workflows/stocko-pp450-schedule.yml
- RR1001: https://github.com/Gopij1987/TT_Token_Gen/actions/workflows/stocko-rr1001-schedule.yml

---

## Troubleshooting

**"Secret not found" error:**
→ Check secret name matches exactly (case-sensitive)  
→ Make sure secret is added to correct repository

**Workflow doesn't run at scheduled time:**
→ Check Actions are enabled in Settings  
→ Workflows only run on default branch (main)  
→ Cron job might run within an hour of scheduled time (GitHub's SLA)

**Wrong user logging in:**
→ Verify `USER_ID` env var in workflow matches username  
→ Check correct secrets are set for that user
