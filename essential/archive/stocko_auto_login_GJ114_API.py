"""
Stocko Broker Auto Login - API Version (GJ114 API)
Direct HTTP API calls - NO BROWSER NEEDED
Fast execution: ~5-10 seconds vs 65 seconds with browser
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from pyotp import TOTP
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import re

# Load environment variables
dotenv_path = Path(__file__).parent / '.env.GJ114'
load_dotenv(dotenv_path)

# Telegram notification function
def send_telegram_notification(tag, username, auth_code, success=True, duration=None, totp_code=None, final_url=None):
    """Send Telegram notification"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print(f"[{tag}] Telegram not configured")
            return
        
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        timestamp = now_ist.strftime("%Y-%m-%d %H:%M:%S")
        
        if success:
            message = f"<b>🚀 {tag} API Login Success!</b>\n"
        else:
            message = f"<b>❌ {tag} API Login Failed!</b>\n"

        message += f"👤 <b>Account:</b> <code>{username}</code>\n"
        message += f"🔑 <b>Auth:</b> <code>{auth_code}</code>\n"
        message += f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"

        if success:
            message += "\n<b>🔐 Login</b>\n"
            if totp_code:
                message += f"• <b>TOTP:</b> <code>{totp_code}</code>\n"
            if duration:
                message += f"• <b>⏳ Duration:</b> <code>{duration:.1f}s</code>\n"
            message += f"• <b>🖥️ Type:</b> <code>API (No Browser)</code>\n"
            if final_url:
                message += f"• <b>🔗 URL:</b> <code>{final_url.split('?')[0]}</code>\n"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print(f"[{tag}] ✓ Telegram notification sent!")
        else:
            print(f"[{tag}] Warning: Telegram failed - {response.status_code}")
    except Exception as e:
        print(f"[{tag}] Warning: Telegram error - {e}")


class StockoAPILogin:
    def __init__(self):
        self.base_url_tradetron = "https://sasstocko.broker.tradetron.tech"
        self.base_url_api = "https://api.stocko.in"
        self.tag = "GJ114-API"
        self.session = requests.Session()
        
        # Set headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_totp_code(self):
        """Generate TOTP code"""
        totp_secret = os.getenv('STOCKO_TOTP_SECRET')
        if not totp_secret:
            print(f"[{self.tag}] ERROR: STOCKO_TOTP_SECRET not set")
            sys.exit(1)
        code = TOTP(totp_secret).now()
        print(f"[{self.tag}] Generated TOTP: {code}")
        return code

    def login(self, auth_code):
        """
        Perform OAuth login using direct API calls
        
        Flow:
        1. GET /auth/{auth_code} → Get login URL
        2. GET /oauth/login?login_challenge=... → Get login form
        3. POST /oauth/login → Submit credentials
        4. POST /oauth/twofa → Submit TOTP
        5. GET /success → Verify success
        """
        
        start_time = time.time()
        username = os.getenv('STOCKO_USERNAME')
        password = os.getenv('STOCKO_PASSWORD')
        totp_code = None
        
        try:
            print("\n" + "="*70)
            print(f"[{self.tag}] ═══════════════════════════════════════════════════════════")
            print(f"[{self.tag}] STOCKO BROKER AUTO LOGIN - API VERSION")
            print(f"[{self.tag}] ═══════════════════════════════════════════════════════════")
            print(f"[{self.tag}] Starting API-based authentication...")
            print("="*70)
            
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Initial auth endpoint
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 1: Getting OAuth challenge...")
            auth_url = f"{self.base_url_tradetron}/auth/{auth_code}"
            print(f"[{self.tag}] GET {auth_url}")
            
            response = self.session.get(auth_url, allow_redirects=False)
            print(f"[{self.tag}] Status: {response.status_code}")
            print(f"[{self.tag}] Cookies: {dict(self.session.cookies)}")
            
            # Get login challenge from redirect or response
            if 'login_challenge' in response.text:
                match = re.search(r'login_challenge=([a-f0-9]+)', response.text)
                if match:
                    login_challenge = match.group(1)
                    print(f"[{self.tag}] Challenge: {login_challenge}")

            # ═══════════════════════════════════════════════════════════
            # STEP 2: Get login form (to extract tokens)
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 2: Getting login form...")
            
            # Try to find the actual login form URL
            login_form_url = f"{self.base_url_api}/oauth/login?login_challenge={auth_code if not 'login_challenge' in response.text else auth_code}"
            print(f"[{self.tag}] GET {login_form_url}")
            
            form_response = self.session.get(login_form_url, allow_redirects=True)
            print(f"[{self.tag}] Status: {form_response.status_code}")
            
            # Extract CSRF token and challenge from form
            csrf_match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', form_response.text)
            challenge_match = re.search(r'name="login_challenge"\s+value="([^"]+)"', form_response.text)
            
            csrf_token = csrf_match.group(1) if csrf_match else None
            challenge = challenge_match.group(1) if challenge_match else auth_code
            
            print(f"[{self.tag}] CSRF Token: {csrf_token[:20]}..." if csrf_token else f"[{self.tag}] CSRF Token: Not found")
            print(f"[{self.tag}] Challenge: {challenge}")

            # ═══════════════════════════════════════════════════════════
            # STEP 3: Submit login credentials
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 3: Submitting credentials...")
            print(f"[{self.tag}] Username: {username}")
            
            login_data = {
                'login_id': username,
                'password': password,
                'login_challenge': challenge,
            }
            if csrf_token:
                login_data['_csrf_token'] = csrf_token
            
            login_response = self.session.post(
                form_response.url,
                data=login_data,
                allow_redirects=True
            )
            print(f"[{self.tag}] POST {form_response.url}")
            print(f"[{self.tag}] Status: {login_response.status_code}")
            print(f"[{self.tag}] Final URL: {login_response.url[:70]}...")
            
            # Check for login errors
            if 'error' in login_response.text.lower() or 'invalid' in login_response.text.lower():
                print(f"[{self.tag}] ❌ Login error detected")
                send_telegram_notification(self.tag, username, auth_code, success=False)
                return False

            # ═══════════════════════════════════════════════════════════
            # STEP 4: Get TOTP form and submit TOTP
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 4: Getting TOTP form...")
            
            totp_page = self.session.get(login_response.url)
            print(f"[{self.tag}] Status: {totp_page.status_code}")
            
            # Check if we're on TOTP page
            if 'twofa' not in totp_page.url and 'totp' not in totp_page.text.lower():
                print(f"[{self.tag}] ⚠️  Not on TOTP page yet")
                print(f"[{self.tag}] Current URL: {totp_page.url[:70]}...")
            
            # Extract TOTP form data
            twofa_token_match = re.search(r'twofa_token=([a-zA-Z0-9_-]+)', totp_page.url)
            if not twofa_token_match:
                twofa_token_match = re.search(r'name="twofa_token"\s+value="([^"]+)"', totp_page.text)
            
            twofa_token = twofa_token_match.group(1) if twofa_token_match else None
            print(f"[{self.tag}] 2FA Token: {twofa_token[:20]}..." if twofa_token else f"[{self.tag}] 2FA Token: Not found")
            
            # Generate TOTP
            print(f"\n[{self.tag}] STEP 5: Submitting TOTP...")
            totp_code = self.get_totp_code()
            
            totp_data = {
                'answers[]': totp_code,
            }
            if twofa_token:
                totp_data['twofa_token'] = twofa_token
            
            totp_response = self.session.post(
                totp_page.url,
                data=totp_data,
                allow_redirects=True
            )
            print(f"[{self.tag}] POST {totp_page.url[:70]}...")
            print(f"[{self.tag}] Status: {totp_response.status_code}")
            print(f"[{self.tag}] Final URL: {totp_response.url[:70]}...")
            
            # Check for TOTP errors
            if 'invalid' in totp_response.text.lower() or 'error' in totp_response.text.lower():
                print(f"[{self.tag}] ❌ TOTP error detected")
                # Could retry here, but for now just report failure
                send_telegram_notification(self.tag, username, auth_code, success=False, totp_code=totp_code)
                return False

            # ═══════════════════════════════════════════════════════════
            # STEP 6: Verify success
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 6: Verifying success...")
            
            # Check if we're on success page
            if 'success' in totp_response.url.lower() or 'success' in totp_response.text.lower():
                duration = time.time() - start_time
                print(f"\n[{self.tag}] ═══════════════════════════════════════════════════════════")
                print(f"[{self.tag}] ✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
                print(f"[{self.tag}] ═══════════════════════════════════════════════════════════")
                print(f"[{self.tag}] ✓ Final URL: {totp_response.url}")
                print(f"[{self.tag}] ✓ Total Duration: {duration:.1f} seconds")
                print(f"[{self.tag}] ✓ TOTP Used: {totp_code}")
                
                send_telegram_notification(
                    self.tag, username, auth_code,
                    success=True,
                    duration=duration,
                    totp_code=totp_code,
                    final_url=totp_response.url
                )
                
                return True
            else:
                print(f"[{self.tag}] ❌ Success page not detected")
                print(f"[{self.tag}] Current URL: {totp_response.url}")
                print(f"[{self.tag}] Page content (first 300 chars): {totp_response.text[:300]}")
                send_telegram_notification(self.tag, username, auth_code, success=False, totp_code=totp_code)
                return False

        except Exception as e:
            print(f"\n[{self.tag}] ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            send_telegram_notification(self.tag, username, auth_code, success=False)
            return False


def main():
    auth_code = os.getenv('STOCKO_AUTH_CODE')
    if not auth_code:
        print("ERROR: STOCKO_AUTH_CODE not set in .env.GJ114")
        sys.exit(1)

    login = StockoAPILogin()
    result = login.login(auth_code)
    
    if result:
        print(f"\n[GJ114-API] ✅ SCRIPT COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"\n[GJ114-API] ❌ SCRIPT FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
