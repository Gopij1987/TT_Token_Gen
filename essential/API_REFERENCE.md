# API Endpoints Reference

## Algosense Login API ✅ VERIFIED

**Endpoint:** `POST https://api.algotest.in/login`

**Headers:**
```
Content-Type: application/json
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Connection: keep-alive
Origin: https://algotest.in
Referer: https://algotest.in/login
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-site
```

**Request Payload:**
```json
{
  "phoneNumber": "+91XXXXXXXXXX",
  "password": "your_password"
}
```

**Example (Real):**
```json
{
  "phoneNumber": "+919940044222",
  "password": "Gopi@2026"
}
```

**Response (Success - 200):**
```json
{
  "login": true,
  "data": {
    "_id": "6746af5b113344e8c1241d43",
    "username": "Goji J",
    "experience_set": true,
    "signup_date": "2024-11-27T05:34:19.958"
  }
}
```

**Response Cookies:**
```
access_token_cookie: eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9...
csrf_access_token: 955b6af6-a6d4-4eef-a0cb-89f7c9bc4588
```

**Response (Error - 400):**
```json
{
  "schema_error": "'phoneNumber' is a required property"
}
```

OR

```json
{
  "schema_error": "'9940044222' does not match '^\\+91\\d{10}$'"
}
```

**Validation Rules:**
- `phoneNumber` field is REQUIRED (not `phone` or `username`)
- Format: Must match regex `^\\+91\\d{10}$`
  - Must start with `+91`
  - Followed by exactly 10 digits
  - Example: `+919940044222` ✅
  - Example: `9940044222` ❌
  - Example: `919940044222` ❌

**Performance:**
- Duration: ~1.1-1.5 seconds
- Success rate: Consistent
- No browser required

**Python Implementation:**
```python
import requests

session = requests.Session()
phone = "+91" + "9940044222"  # Format with +91 prefix
payload = {"phoneNumber": phone, "password": "Gopi@2026"}

response = session.post(
    "https://api.algotest.in/login",
    json=payload,
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    if result.get('login') is True:
        print("✅ Login successful")
        # Cookies automatically stored in session.cookies
```

---

## Broker Login API 🟡 PENDING DISCOVERY

**Status:** Not yet captured

**Expected Location:** 
- URL: `https://algotest.in/broker` (My Brokers tab)
- Trigger: Click "Login" button for IIFL Markets
- Broker Identifier: Likely "IIFL" or similar ID

**Discovery Method:**
```bash
python discover_broker_login.py
```

**Will Capture:**
- API endpoint URL
- Request method (POST/GET)
- Required headers
- Payload format
- Response format
- Session cookies/tokens

**Expected Result File:**
- `broker_api_calls.json` - Detailed network requests
- `broker_before_login.png` - Screenshot before click
- `broker_after_login.png` - Screenshot after click

---

## Session Management

### Preserve Session for Reuse
```python
# Save session after login
import json
from pathlib import Path

session_data = {
    'cookies': dict(session.cookies),
    'headers': dict(session.headers),
    'endpoint': 'https://api.algotest.in/login'
}

with open('.session.json', 'w') as f:
    json.dump(session_data, f)

# Reload session
session = requests.Session()
for name, value in session_data['cookies'].items():
    session.cookies.set(name, value)
```

### Transfer to Selenium
```python
# Transfer requests.Session cookies to Selenium driver
session = requests.Session()
# ... perform login ...

driver.get("https://algotest.in/")
for name, value in session.cookies.items():
    driver.add_cookie({'name': name, 'value': value, 'domain': 'algotest.in', 'path': '/'})
```

---

## Testing Credentials

**Account:** Goji J  
**Phone:** 9940044222 (stored as: +919940044222 in API)  
**Password:** Gopi@2026  
**Brokers:** 2 configured
- Bigul Gopi (NSE, BSE) - LOGGED IN
- IIFL Markets (NSE, BSE) - LOGGED OUT (needs re-login)

---

## Environment Variables

**File:** `.env.algosense`

```
# Algosense Credentials
ALGOSENSE_USERNAME=9940044222
ALGOSENSE_PASSWORD=Gopi@2026

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Broker Credentials (To be determined)
BROKER_USERNAME=
BROKER_PASSWORD=
```

---

## Troubleshooting

### Error: "'phoneNumber' is a required property"
**Cause:** Field name is wrong (using `phone` or `username`)  
**Fix:** Use `phoneNumber` instead

### Error: "does not match '^\\+91\\d{10}$'"
**Cause:** Phone format is invalid  
**Fix:** 
- Ensure format: `+91` + 10 digits
- Remove leading zeros if present
- Example: `9940044222` → `+919940044222`

### Error: HTTP 401 Unauthorized
**Cause:** Invalid credentials  
**Fix:** Verify username/password in `.env.algosense`

### Error: Connection timeout
**Cause:** Network issue or server down  
**Fix:** Check internet connection, try again

### Selenium can't find elements
**Cause:** JavaScript not rendered yet  
**Fix:** Increase `WebDriverWait` timeout (currently 15 seconds)

---

**Last Updated:** 2026-02-13  
**Status:** In Active Development
