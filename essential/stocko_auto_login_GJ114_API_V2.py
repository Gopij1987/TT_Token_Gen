"""
Stocko Broker Auto Login - Improved API Version (GJ114 API V2)
Better form field extraction and OAuth handling

Usage:
  Local:  python stocko_auto_login_GJ114_API_V2.py (uses .env.GJ114)
  GitHub: Uses 'GJ114_*' environment secrets
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
from bs4 import BeautifulSoup

# Determine which user config to load
USER_ID = os.getenv('USER_ID', 'GJ114')  # Default to GJ114, can override with env var

# Load environment variables from .env file (local development)
dotenv_path = Path(__file__).parent / f'.env.{USER_ID}'
load_dotenv(dotenv_path)

# Define credential variables (simplified - just one format now)
def get_credential(key):
    """Get credential from environment using GitHub Secrets naming convention"""
    # Format: <USER_ID>_<KEY> (e.g., GJ114_USERNAME, PP450_PASSWORD)
    env_key = f"{USER_ID}_{key}"
    value = os.getenv(env_key)
    if value:
        return value
    return None

def send_telegram_notification(tag, username, auth_code, success=True, duration=None, totp_code=None, final_url=None, error_message=None):
    """Send Telegram notification"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            return
        
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        timestamp = now_ist.strftime("%Y-%m-%d %H:%M:%S")
        
        if success:
            message = f"<b>🚀 Token Generated!</b>\n"
        else:
            message = f"<b>❌ {tag} API Login Failed!</b>\n"

        message += f"👤 <b>Account:</b> <code>{username}</code>\n"
        message += f"🔑 <b>Auth:</b> <code>{auth_code}</code>\n"
        message += f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"

        if success:
            message += "\n<b>🔐 Token Generated</b>\n"
            if totp_code:
                message += f"• <b>TOTP:</b> <code>{totp_code}</code>\n"
            if duration:
                message += f"• <b>⏳ Duration:</b> <code>{duration:.1f}s</code>\n"
            message += f"• <b>🖥️ Type:</b> <code>API (No Browser)</code>\n"
            if final_url:
                message += f"• <b>🔗 URL:</b> <code>{final_url.split('?')[0]}</code>\n"
        else:
            message += "\n<b>❗ Error Details:</b>\n"
            if error_message:
                # Limit error message length to avoid Telegram limits
                error_text = str(error_message)[:200]
                message += f"• <b>Error:</b> <code>{error_text}</code>\n"
            else:
                message += "• <b>Error:</b> <code>Unknown error occurred</code>\n"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=5)
    except:
        pass


class StockoAPILoginV2:
    def __init__(self):
        self.base_url = "https://sasstocko.broker.tradetron.tech"
        self.api_url = "https://api.stocko.in"
        self.tag = "GJ114-API-V2"
        self.session = requests.Session()
        
        # Set realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

    def extract_form_fields(self, html):
        """Extract ALL form fields from HTML using BeautifulSoup"""
        try:
            if not html or not isinstance(html, str):
                print(f"[{self.tag}] ❌ Invalid HTML content")
                return {}
                
            soup = BeautifulSoup(html, 'html.parser')
            form = soup.find('form')
            if not form:
                print(f"[{self.tag}] ⚠️  No form found in HTML")
                return {}
            
            fields = {}
            # Extract all input fields
            for input_field in form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    fields[name] = value
                    display_val = value[:30] if len(str(value)) > 30 else value
                    print(f"[{self.tag}] Found field: {name}={display_val}")
            
            if not fields:
                print(f"[{self.tag}] ⚠️  No input fields found in form")
                return {}
            
            return fields
        except Exception as e:
            print(f"[{self.tag}] ❌ Error extracting form fields: {e}")
            return {}

    def get_totp_code(self):
        """Generate TOTP code"""
        try:
            totp_secret = get_credential('TOTP_SECRET')
            if not totp_secret:
                print(f"[{self.tag}] ❌ TOTP_SECRET not set for user {USER_ID}")
                raise ValueError("TOTP secret missing")
            code = TOTP(totp_secret).now()
            print(f"[{self.tag}] Generated TOTP: {code}")
            return code
        except Exception as e:
            print(f"[{self.tag}] ❌ Error generating TOTP: {e}")
            raise
    
    def submit_totp_with_retry(self, totp_url, totp_form_fields, username, auth_code, max_retries=1):
        """Submit TOTP with retry logic (1 retry after 30sec wait)"""
        self.last_totp_code = None  # Store last TOTP code
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"\n[{self.tag}] ⏳ TOTP Retry {attempt}/{max_retries}")
                    print(f"[{self.tag}] Waiting 30 seconds before retry...")
                    time.sleep(30)
                
                print(f"\n[{self.tag}] STEP 5: Submitting TOTP (Attempt {attempt + 1}/{max_retries + 1})...")
                
                totp_code = self.get_totp_code()
                self.last_totp_code = totp_code  # Store for later use
                totp_data = totp_form_fields.copy()
                totp_data['answers[]'] = totp_code
                
                print(f"[{self.tag}] TOTP Form data keys: {list(totp_data.keys())}")
                
                totp_response = self.session.post(
                    totp_url,
                    data=totp_data,
                    allow_redirects=True,
                    timeout=30
                )
                
                print(f"[{self.tag}] POST {totp_url}")
                print(f"[{self.tag}] Status: {totp_response.status_code}")
                print(f"[{self.tag}] Final URL: {totp_response.url}")
                
                # Validate response
                if totp_response.status_code >= 400:
                    error_msg = f"HTTP {totp_response.status_code}: {totp_response.text[:100]}"
                    print(f"[{self.tag}] ⚠️  TOTP request failed: {totp_response.status_code}")
                    if attempt < max_retries:
                        print(f"[{self.tag}] Will retry after waiting...")
                        continue
                    else:
                        print(f"[{self.tag}] ❌ Max retries exhausted")
                        send_telegram_notification(self.tag, username, auth_code, success=False, totp_code=totp_code, error_message=error_msg)
                        return None
                
                # Check for invalid TOTP
                if 'invalid' in totp_response.text.lower() or 'incorrect' in totp_response.text.lower():
                    error_msg = "Invalid TOTP code - server rejected"
                    print(f"[{self.tag}] ⚠️  TOTP invalid error detected")
                    if attempt < max_retries:
                        print(f"[{self.tag}] Will retry with new TOTP...")
                        continue
                    else:
                        print(f"[{self.tag}] ❌ TOTP failed after {max_retries + 1} attempts")
                        send_telegram_notification(self.tag, username, auth_code, success=False, totp_code=totp_code, error_message=error_msg)
                        return None
                
                # Success - return response
                return totp_response
                
            except requests.Timeout:
                error_msg = "TOTP request timeout (30 sec)"
                print(f"[{self.tag}] ⚠️  TOTP request timeout")
                if attempt < max_retries:
                    print(f"[{self.tag}] Will retry...")
                    continue
                else:
                    print(f"[{self.tag}] ❌ Timeout after {max_retries + 1} attempts")
                    send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                    return None
            except Exception as e:
                error_msg = f"TOTP error: {str(e)[:100]}"
                print(f"[{self.tag}] ❌ TOTP error: {e}")
                if attempt < max_retries:
                    print(f"[{self.tag}] Will retry...")
                    continue
                else:
                    print(f"[{self.tag}] ❌ Error after {max_retries + 1} attempts")
                    send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                    return None
        
        return None

    def login(self, auth_code=None):
        """Perform OAuth login using improved API approach"""
        
        # Use provided auth_code or get from credentials
        if not auth_code:
            auth_code = get_credential('AUTH_CODE')
        
        start_time = time.time()
        username = get_credential('USERNAME')
        password = get_credential('PASSWORD')
        totp_code = None
        
        try:
            print("\n" + "="*70)
            print(f"[{self.tag}] ═══════════════════════════════════════════════════════════")
            print(f"[{self.tag}] STOCKO BROKER AUTO LOGIN - IMPROVED API VERSION")
            print(f"[{self.tag}] ═══════════════════════════════════════════════════════════")
            print("="*70)
            
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Initial auth endpoint
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 1: Getting OAuth challenge...")
            auth_url = f"{self.base_url}/auth/{auth_code}"
            print(f"[{self.tag}] GET {auth_url}")
            
            response = self.session.get(auth_url, allow_redirects=True, timeout=30)
            print(f"[{self.tag}] Status: {response.status_code}")
            print(f"[{self.tag}] Final URL: {response.url}")
            print(f"[{self.tag}] Cookies: {list(self.session.cookies.keys())}")
            
            # Validate initial response
            if response.status_code >= 400:
                error_msg = f"OAuth challenge failed: HTTP {response.status_code}"
                print(f"[{self.tag}] ❌ Initial request failed: {response.status_code}")
                send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                return False
            
            # ═══════════════════════════════════════════════════════════
            # STEP 2: Extract form fields from login page
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 2: Extracting form fields...")
            
            form_fields = self.extract_form_fields(response.text)
            
            if not form_fields:
                print(f"[{self.tag}] ❌ Could not extract form fields")
                return False
            
            # ═══════════════════════════════════════════════════════════
            # STEP 3: Prepare and submit login credentials
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 3: Submitting credentials...")
            print(f"[{self.tag}] Username: {username}")
            
            # Update form fields with credentials
            login_data = form_fields.copy()
            login_data['login_id'] = username
            login_data['password'] = password
            
            print(f"[{self.tag}] Form data keys: {list(login_data.keys())}")
            
            login_response = self.session.post(
                response.url,
                data=login_data,
                allow_redirects=True,
                timeout=30
            )
            print(f"[{self.tag}] POST {response.url}")
            print(f"[{self.tag}] Status: {login_response.status_code}")
            print(f"[{self.tag}] Final URL: {login_response.url}")
            
            # Check for errors
            if login_response.status_code >= 400:
                error_msg = f"HTTP {login_response.status_code}: {login_response.text[:100]}"
                print(f"[{self.tag}] ❌ Login request failed: {login_response.status_code}")
                print(f"[{self.tag}] Response: {login_response.text[:200]}")
                send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                return False
            
            # Better error detection - look for error page patterns
            text_lower = login_response.text.lower()
            if 'invalid credentials' in text_lower or 'login failed' in text_lower or '<error>' in text_lower:
                print(f"[{self.tag}] ❌ Login error detected in response")
                return False
            
            if login_response.url.startswith(self.api_url + "/oauth/twofa"):
                print(f"[{self.tag}] ✅ Successfully redirected to TOTP page!")
            else:
                # Check if still on login page (means credentials failed)
                if '/oauth/login' in login_response.url:
                    error_msg = "Invalid credentials - server rejected username/password"
                    print(f"[{self.tag}] ❌ Still on login page - credentials rejected!")
                    print(f"[{self.tag}] The server did not redirect to TOTP page")
                    send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                    return False
                else:
                    print(f"[{self.tag}] ⚠️  Unexpected URL after login: {login_response.url}")
                    print(f"[{self.tag}] Expected: {self.api_url}/oauth/twofa")

            # ═══════════════════════════════════════════════════════════
            # STEP 4: Get TOTP form
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 4: Getting TOTP form...")
            
            # Check if we're on TOTP page
            if 'twofa' not in login_response.url.lower():
                error_msg = f"Not on TOTP page. Got URL: {login_response.url[:80]}..."
                print(f"[{self.tag}] ❌ ERROR: Not on TOTP page!")
                print(f"[{self.tag}] Expected URL containing 'twofa'")
                print(f"[{self.tag}] Got URL: {login_response.url}")
                send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                return False
            
            totp_form_fields = self.extract_form_fields(login_response.text)
            
            if not totp_form_fields or 'answers[]' not in totp_form_fields:
                error_msg = f"TOTP form field not found. Available: {', '.join(list(totp_form_fields.keys())[:5])}"
                print(f"[{self.tag}] ⚠️  Could not find TOTP input field")
                print(f"[{self.tag}] Available fields: {list(totp_form_fields.keys())}")
                send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                return False
            
            # ═══════════════════════════════════════════════════════════
            # STEP 5: Generate and submit TOTP (with retry logic)
            # ═══════════════════════════════════════════════════════════
            totp_response = self.submit_totp_with_retry(
                login_response.url,
                totp_form_fields,
                username,
                auth_code,
                max_retries=1
            )
            
            if not totp_response:
                return False

            # ═══════════════════════════════════════════════════════════
            # STEP 6: Verify success
            # ═══════════════════════════════════════════════════════════
            print(f"\n[{self.tag}] STEP 6: Verifying success...")
            
            # Validate final response
            if totp_response.status_code >= 400:
                error_msg = f"Final verification failed: HTTP {totp_response.status_code}"
                print(f"[{self.tag}] ❌ Final response error: {totp_response.status_code}")
                send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                return False
            
            final_url = totp_response.url
            final_text = totp_response.text.lower()
            
            # Validate we got HTML response
            if not final_text or len(final_text) < 10:
                error_msg = "Empty or invalid final response"
                print(f"[{self.tag}] ❌ Response too small or empty")
                send_telegram_notification(self.tag, username, auth_code, success=False, error_message=error_msg)
                return False
            
            # Strict success check
            is_success_url = 'success' in final_url.lower()
            is_success_text = 'success' in final_text
            
            if is_success_url or is_success_text:
                duration = time.time() - start_time
                print(f"\n[{self.tag}] ═══════════════════════════════════════════════════════════")
                print(f"[{self.tag}] ✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
                print(f"[{self.tag}] ═══════════════════════════════════════════════════════════")
                print(f"[{self.tag}] ✓ Final URL: {final_url}")
                print(f"[{self.tag}] ✓ Total Duration: {duration:.1f} seconds")
                if hasattr(self, 'last_totp_code'):
                    print(f"[{self.tag}] ✓ TOTP Used: {self.last_totp_code}")
                
                send_telegram_notification(
                    self.tag, username, auth_code,
                    success=True,
                    duration=duration,
                    totp_code=self.last_totp_code if hasattr(self, 'last_totp_code') else None,
                    final_url=final_url
                )
                
                return True
            else:
                error_msg = f"Login verification failed. Final URL: {final_url[:80]}... - No 'success' indicator found"
                print(f"[{self.tag}] ❌ SUCCESS NOT VERIFIED")
                print(f"[{self.tag}] Final URL: {final_url}")
                print(f"[{self.tag}] Contains 'success' in URL: {is_success_url}")
                print(f"[{self.tag}] Contains 'success' in text: {is_success_text}")
                print(f"[{self.tag}] Content (first 300 chars): {totp_response.text[:300]}")
                send_telegram_notification(self.tag, username, auth_code, success=False, totp_code=self.last_totp_code if hasattr(self, 'last_totp_code') else None, error_message=error_msg)
                return False

        except Exception as e:
            error_msg = f"Exception: {str(e)[:100]}"
            print(f"\n[{self.tag}] ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            # Try to send notification about the exception
            try:
                send_telegram_notification(
                    self.tag, username, auth_code, 
                    success=False, 
                    error_message=error_msg
                )
            except:
                pass
            return False


def main():
    # Check for BeautifulSoup
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("ERROR: BeautifulSoup4 not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    
    # Get auth code
    auth_code = get_credential('AUTH_CODE')
    if not auth_code:
        print(f"ERROR: AUTH_CODE not set for user {USER_ID}")
        print(f"Checked: {USER_ID}_AUTH_CODE or STOCKO_AUTH_CODE")
        print(f"Make sure .env.{USER_ID} file exists or GitHub Secrets are configured")
        sys.exit(1)

    print(f"[INFO] Using user config: {USER_ID}")
    login = StockoAPILoginV2()
    result = login.login(auth_code)
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
