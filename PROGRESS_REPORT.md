# AlgoTest Autologin - Progress Report

**Date:** February 13, 2026  
**Status:** In Progress  

---

## ✅ Completed Tasks

### 1. Algosense Account Autologin (WORKING)
- **File:** `algosense_auto_login.py`
- **Method:** Pure API (no browser required)
- **Endpoint:** `POST https://api.algotest.in/login`
- **Performance:** 1.5 seconds
- **Status:** ✅ **FULLY FUNCTIONAL**

**Key Details:**
- Phone format: Must use `+91` prefix (e.g., `+919940044222`)
- Payload: `{"phoneNumber": "+91...", "password": "..."}`
- Returns: JWT token in `access_token_cookie` + CSRF token
- Session saved to: `.algosense_session.json`

**Credentials:**
- Username (Phone): `9940044222`
- Password: `Gopi@2026`
- Env file: `.env.algosense`

**Test Results:**
```
Status: 200
Response: {
  "login": true,
  "data": {
    "_id": "6746af5b113344e8c1241d43",
    "username": "Goji J",
    "experience_set": true,
    "signup_date": "2024-11-27T05:34:19.958"
  }
}
Duration: 1.5 seconds
Cookies: 2 (access_token_cookie, csrf_access_token)
```

### 2. Bigul Broker Login Discovery (IN PROGRESS)
- **File:** `discover_broker_login.py` (updated for Bigul)
- **Objective:** Find API endpoint for Bigul broker login
- **Task:** Navigate to /broker → My Brokers tab → Find Bigul card → Capture login API
- **Status:** 🟡 **READY TO TEST AT MARKET OPEN**

**What Works:**
- ✓ Algosense login via API
- ✓ Session transfer to Selenium browser
- ✓ Navigation to /broker page
- ✓ Clicking "My Brokers" tab
- ✓ Finding Bigul card (NSE, BSE)
- ✓ Locating Bigul action button

**Current Status:**
- ⏳ Button is **DISABLED** because market is currently CLOSED
- ⏳ Button text: "Market Closed"
- ⏳ Will become **ENABLED** when market opens (9:15 AM IST)

**Testing Plan:**
1. Market opens → Button auto-enables
2. Run script again during market hours
3. Capture network requests when "Login" button becomes clickable
4. Extract Bigul API endpoint, headers, and payload format
5. Create `bigul_auto_login.py` similar to `algosense_auto_login.py`

**Available Discovery Scripts:**
- `discover_broker_login.py` - Interactive Selenium + CDP capture
- `bigul_api_discovery.py` - Pattern analysis + common endpoints

---

## 📁 File Structure

```
essential/
├── algosense_auto_login.py          ✅ WORKING
├── algosense_auto_login_api.py      ✅ REFERENCE
├── algosense_auto_login_selenium.py ✅ REFERENCE
├── discover_broker_login.py         🟡 BIGUL - READY FOR MARKET OPEN
├── bigul_api_discovery.py           🆕 PATTERN ANALYSIS HELPER
├── find_broker_api.py               📝 ANALYSIS
├── find_broker_api_v2.py            📝 ANALYSIS
├── .algosense_session.json          📄 SESSION DATA
├── broker_page.html                 📄 CAPTURED HTML
├── broker_page_bigul.html           📄 BIGUL PAGE (Market Closed)
├── broker_api_calls.json            📄 (to be populated)
└── requirements_gj114.txt           📦 DEPENDENCIES
```

---

## 🔧 Environment Setup

**Virtual Environment:** `.venv` (Python 3.14.2)

**Key Packages Installed:**
- `requests` - HTTP requests for API calls
- `selenium` - Browser automation
- `webdriver-manager` - Chrome driver management
- `python-dotenv` - Environment variables
- `beautifulsoup4` - HTML parsing

**Credentials (in `.env.algosense`):**
```
ALGOSENSE_USERNAME=9940044222
ALGOSENSE_PASSWORD=Gopi@2026
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---

## 🎯 Next Steps

### Priority 1: Complete Broker Login Discovery
1. Run `discover_broker_login.py` to completion
2. Extract the broker login API endpoint from captured requests
3. Document the payload format

### Priority 2: Create Broker Autologin Script
1. Create `broker_auto_login.py` file
2. Implement IIFL Markets login using discovered API
3. Test and verify success

### Priority 3: Combine into Complete Flow
1. Update main autologin to:
   - Login to Algosense (✅ done)
   - Navigate to /broker (new)
   - Click My Brokers tab (new)
   - Click IIFL Markets Login (new)
   - Verify broker session (new)

---

## 📊 API Endpoints Discovered

### 1. Algosense Login ✅
```
Method: POST
URL: https://api.algotest.in/login
Headers:
  Content-Type: application/json
  User-Agent: Mozilla/5.0...
  Origin: https://algotest.in
  Referer: https://algotest.in/login

Payload:
{
  "phoneNumber": "+91XXXXXXXXXX",
  "password": "password"
}

Response:
{
  "login": true,
  "data": {...}
}

Cookies Set:
- access_token_cookie (JWT)
- csrf_access_token (GUID)
```

### 2. Broker Login 🟡
- **Status:** Endpoint not yet captured
- **Expected:** Will be discovered when clicking Login button in My Brokers tab
- **File:** `broker_api_calls.json` (to be populated by discovery script)

---

## 💾 Session Management

### Algosense Session
**File:** `.algosense_session.json`
```json
{
  "timestamp": "2026-02-13T08:55:27.352594",
  "username": "9940044222",
  "endpoint": "https://api.algotest.in/login",
  "method": "POST",
  "status_code": 200,
  "cookies": {
    "access_token_cookie": "eyJhbGc...",
    "csrf_access_token": "955b6af6-..."
  },
  "duration_seconds": 1.5
}
```

### Broker Session
**File:** `.broker_session.json` (to be created)
- Will contain: Broker login endpoint, method, cookies, tokens

---

## 🚀 Quick Test Commands

**Test Algosense Login:**
```bash
cd essential
python algosense_auto_login.py
```

**Expected Output:**
```
[ALGOSENSE] ✅✅✅ LOGIN SUCCESSFUL ✅✅✅
[ALGOSENSE] Duration: 1.5 seconds
[ALGOSENSE] Cookies: 2
```

**Discover Broker Login API:**
```bash
python discover_broker_login.py
```

---

## 🔍 Technical Insights

### Phone Number Formatting
The API requires a specific format:
- Input: `9940044222` (Indian number without country code)
- Required Format: `+919940044222` (with +91 prefix)
- Regex Pattern: `^\\+91\\d{10}$`

### Session Persistence
- Algosense API returns JWT token in `access_token_cookie` header
- Must be preserved for subsequent API calls to `api.algotest.in`
- CSRF token provided for protection against attacks

### Browser Automation vs Pure API
- **API Method:** 1.5 seconds, lightweight, no browser needed
- **Selenium Method:** 9.5 seconds, requires Chrome browser
- **Chosen:** API method (6x faster)

---

## 🐛 Known Issues / Blockers

None at this time. Progress on schedule.

---

## 📅 Market Hours Testing Plan (BIGUL)

**When:** Market opens (9:15 AM IST - 3:45 PM IST)  
**What:** Bigul Login button will be ENABLED  
**How:** Run discovery script to capture API endpoint

**Step-by-Step:**
1. During market hours, run: `python essential/discover_broker_login.py`
2. Script will navigate to /broker → My Brokers → Bigul card
3. Button will be enabled (not "Market Closed")
4. Click the button and capture network request
5. Extract API endpoint from captured logs
6. Create `bigul_auto_login.py` based on discovered endpoint

**Expected Output:**
- API endpoint URL (e.g., `https://api.bigul.com/login` or similar)
- Request method (POST/GET)
- Required headers and payload format
- Response structure with authentication token

**Next Action:**
- Test on next market session: **Monday, Feb 17, 2026 @ 9:15 AM IST**

---

## 📝 Notes

- Broker page is a **Next.js SPA** (JavaScript-rendered, no static HTML form)
- Login buttons are dynamic elements created by React
- Network capture via Chrome DevTools Protocol required to see API calls
- Cookies must be properly transferred from `requests.Session` to Selenium for organic flow

---

**Last Updated:** 2026-02-13 08:55:27 IST  
**Prepared By:** Agent  
**Next Review:** Upon broker API discovery completion
