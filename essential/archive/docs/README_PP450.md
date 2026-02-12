# Stocko Broker Auto Login - PP450

Automated OAuth authentication script for Stocko via Tradetron broker.

**Tag: PP450**

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python stocko_auto_login.py
```

The script will:
1. Prompt for the auth code (or use the default: 733517)
2. Ask for your username/email and password
3. Ask for your TOTP (2FA) code
4. Complete the OAuth flow automatically via Tradetron
5. Save any access tokens to `tokens.json`

**Default URL**: https://sasstocko.broker.tradetron.tech/auth/733517

## Features

- ✅ Handles Tradetron broker authentication flow (PP450)
- ✅ TOTP (2FA) support
- ✅ Saves username for convenience (never saves passwords)
- ✅ Extracts and saves access tokens
- ✅ Session management
- ✅ Error handling
- ✅ Tagged with PP450 for easy identification

## Security

- Passwords are never saved to disk
- Tokens are stored in `tokens.json` (excluded from git)
- Username can be optionally saved in `config.json`
