# API-Based Login Exploration

## Goal
Replace Selenium browser automation with direct API calls for faster, more reliable authentication.

## Known Endpoints
- Base: `https://api.stocko.in/oauth/`
- Login: `https://api.stocko.in/oauth/login`
- TOTP: `https://api.stocko.in/oauth/twofa`
- Success: `https://sasstocko.broker.tradetron.tech/success`

## To Capture API Calls

### Option 1: Browser DevTools Network Tab
1. Open Chrome DevTools (F12)
2. Go to **Network** tab
3. Run the V2 script in **MANUAL MODE** (visible browser)
4. Step through login manually
5. Watch for POST/GET requests and capture:
   - **Request URLs**
   - **Request Headers** (especially Content-Type, User-Agent, Cookies)
   - **Request Body** (form data or JSON)
   - **Response** (HTTP status, headers, body)

### Option 2: Proxy/Interceptor
Use a tool like **Fiddler** or **mitmproxy** to intercept all HTTPS traffic

### Option 3: Selenium + HTTP Logging
Modify our script to log all network traffic

## Expected API Flow

```
POST /oauth/login
├─ Headers: Content-Type, User-Agent, etc.
├─ Body: login_id, password, login_challenge, token
└─ Response: Redirect to /oauth/twofa or error

POST /oauth/twofa
├─ Headers: Cookies (session), etc.
├─ Body: totp_code, twofa_token, etc.
└─ Response: Redirect to success page or error

GET /success
└─ Response: Success page or redirect
```

## Questions to Answer

1. **Are credentials sent as form data or JSON?**
2. **What headers are required?** (User-Agent, Authorization, etc.)
3. **How are sessions managed?** (Cookies, tokens, etc.)
4. **What is the TOTP challenge format?**
5. **What does the success response look like?**

## Implementation Plan

Once we have the API details:

1. Create `stocko_auto_login_API.py` using `requests` library
2. Make direct HTTP calls instead of Selenium
3. Handle:
   - Session management (cookies)
   - CSRF tokens (if any)
   - TOTP generation
   - Error responses
4. Compare performance:
   - Browser: ~65 seconds
   - API: ~5-10 seconds (estimated)

---

## Notes
- Much faster execution
- No stale element errors
- No DOM parsing issues
- Can run on servers without GUI
- Easier to debug with HTTP logs
