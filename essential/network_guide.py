"""
Algosense Login - Network Traffic Analyzer
Helps identify the actual login API endpoints from network traffic

Run this with Selenium to automate network capture and analysis
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)

class NetworkAnalyzer:
    """Analyze network requests to find login API endpoint"""
    
    def __init__(self):
        self.requests = []
        self.tag = "NETWORK-ANALYZER"
    
    def analyze_from_devtools(self):
        """
        INSTRUCTIONS FOR MANUAL CAPTURE:
        
        1. Open Browser DevTools (F12)
        2. Go to Network tab
        3. Clear all requests (Ctrl+L)
        4. Go to https://algotest.in/login
        5. Enter username and password
        6. Click Login button
        7. Watch for ANY of these request types:
        
        PRIORITY 1 - Look for these first:
        ✓ POST /api/login
        ✓ POST /api/auth/login  
        ✓ POST /api/authenticate
        ✓ POST /auth/login
        ✓ POST /login
        ✓ POST /rest/api/login
        
        PRIORITY 2 - If above not found:
        ✓ Any POST request with status 200-302
        ✓ Where Payload tab shows: username, password, email, user_id
        ✓ Where Response tab shows: token, access_token, sessionId, Session-ID
        
        PRIORITY 3 - Check response headers:
        ✓ Set-Cookie (session cookies)
        ✓ Authorization (bearer token)
        ✓ X-Auth-Token
        ✓ X-Session-ID
        
        WHAT TO LOOK FOR:
        ┌─────────────────────────────────────────┐
        │ REQUEST DETAILS                         │
        ├─────────────────────────────────────────┤
        │ URL: https://algotest.in/[ENDPOINT]    │
        │ METHOD: POST                            │
        │ STATUS: 200 or 302                      │
        │                                         │
        │ PAYLOAD (Request Body):                 │
        │ • username: your_username              │
        │ • password: your_password              │
        │ • [other fields...]                    │
        │                                         │
        │ RESPONSE (Response tab):                │
        │ • token: eyJhbGc...                    │
        │ • sessionId: xxx                       │
        │ • success: true                        │
        │ • [other response fields]              │
        │                                         │
        │ RESPONSE HEADERS:                       │
        │ • Set-Cookie: sessionid=xxx            │
        │ • Authorization: Bearer token          │
        └─────────────────────────────────────────┘
        """
        
        instructions = """
╔═══════════════════════════════════════════════════════════════════════════╗
║             ALGOSENSE LOGIN API ENDPOINT IDENTIFICATION GUIDE             ║
╚═══════════════════════════════════════════════════════════════════════════╝

STEP 1: OPEN DEVTOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Windows/Linux: Press F12
  Mac: Cmd + Option + I
  Right-click anywhere → Inspect

STEP 2: SETUP NETWORK MONITORING  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Click "Network" tab
  2. Click the circle button to start recording (red dot shows recording)
  3. Click "Clear" (trash icon) to clear existing requests
  4. DO NOT navigate away yet

STEP 3: TRIGGER LOGIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Go to https://algotest.in/login (in same tab)
  2. Enter your username in the username field
  3. Enter your password in the password field
  4. Click the "Login" button
  5. WATCH THE NETWORK TAB - requests will appear

STEP 4: IDENTIFY THE LOGIN REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Look for FIRST request that:
  ✓ Method = POST (not GET)
  ✓ Status = 200, 201, 301, or 302 (green circle)
  ✓ Name contains: login, auth, authenticate, signin
  ✓ NOT: analytics, cdn, fonts, pixel, mixpanel, gtag

STEP 5: EXAMINE THE REQUEST DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Click on that request row. A panel opens. Check these tabs:
  
  ✓ "Headers" tab:
    • Copy the "Request URL" (e.g., https://algotest.in/api/login)
    • Note "Request Method" (should be POST)
    
  ✓ "Payload" tab:
    • See what data is being sent (username, password, etc.)
    • Copy the form field names
    
  ✓ "Response" tab:
    • See the response body (usually JSON)
    • Look for: token, sessionId, access_token, success
    
  ✓ "Response Headers" tab:
    • Look for: Set-Cookie, Authorization, X-Auth-Token, X-Session-ID

STEP 6: COPY THE ENDPOINT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  From Headers tab:
  • Request URL: ___________________________________________
  • Request Method: ________________________________________
  • Content-Type: __________________________________________
  
  From Payload tab:
  • Field names sent: _______________________________________
  • Example: username, password, _________________________
  
  From Response tab:
  • Response format (JSON/Form): ____________________________
  • Key fields in response: __________________________________
  • Example: token, sessionId, ___________________________

STEP 7: LOOK FOR BROKER LOGIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  After successful login:
  1. You might be redirected to https://algotest.in/broker
  2. Look for a "Login" button on the broker page
  3. Click it and note any NEW API requests that appear
  4. Record those endpoint details too

STEP 8: REPORT FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Share with me:
  
  Main Login API:
  └─ URL: _______________________
  └─ Method: ____________________
  └─ Payload fields: ____________
  └─ Response token field: _______
  
  Broker Login API (if different):
  └─ URL: _______________________
  └─ Method: ____________________
  └─ Payload fields: ____________
  └─ Response fields: ___________

COMMON PATTERNS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pattern 1: REST API style
  POST /api/v1/login
  Payload: { username, password }
  Response: { token, user_id, expires_in }

Pattern 2: Legacy style  
  POST /login
  Payload: { login_id, password, csrf_token }
  Response: { success, session_id }

Pattern 3: OAuth style
  POST /oauth/token
  Payload: { grant_type, username, password, client_id }
  Response: { access_token, token_type }

Pattern 4: Form submission
  POST /login
  Content-Type: application/x-www-form-urlencoded
  Payload: username=x&password=y&_token=z
  Response: Redirect + Set-Cookie

TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Q: I don't see any POST requests after clicking login?
A: • Check if page submitted as regular form (whole page reload)
  • Check "Disable cache" checkbox in DevTools
  • Try Ctrl+Shift+Delete to clear cache before login
  • The request might be named differently (try searching)

Q: I see many requests, how do I know which is login?
A: Look for requests that happen IMMEDIATELY after clicking login button.
   The login request is usually the FIRST request after the click.

Q: The response contains "error" or "invalid credentials"
A: That's still the login endpoint! You found it. Can use same endpoint.
   Just means wrong username/password or server rejected the request.

Q: I see a redirect (302) but no token in response?
A: The token might be in a Set-Cookie header instead.
   Check "Response Headers" tab for "Set-Cookie" with sessionid/token.

╔═══════════════════════════════════════════════════════════════════════════╗
║                     ONCE YOU FIND THE ENDPOINT:                          ║
║         Share the endpoint details below and I'll update the script!      ║
╚═══════════════════════════════════════════════════════════════════════════╝
        """
        
        print(instructions)
        return instructions

def print_guide():
    """Print the network analysis guide"""
    analyzer = NetworkAnalyzer()
    analyzer.analyze_from_devtools()

if __name__ == "__main__":
    print_guide()
