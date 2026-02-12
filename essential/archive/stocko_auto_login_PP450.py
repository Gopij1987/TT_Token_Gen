"""
Stocko Broker Auto Login Script - PP450
Automates the OAuth authentication flow for Stocko via Tradetron
Tag: PP450
Supports: Manual mode & Automated mode (with env variables)
"""

import requests
import json
from urllib.parse import urlparse, parse_qs
import getpass
import os
from pathlib import Path
from pyotp import TOTP
import sys
from datetime import datetime, timezone, timedelta

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# Load environment variables from absolute path
dotenv_path = Path(__file__).parent / '.env.PP450'
load_dotenv(dotenv_path)


def send_telegram_notification(tag, username, auth_code, totp_code=None, final_url=None, duration=None, success=True, last_update_time=None):
    """Send Telegram notification for login with detailed information"""
    try:
        import socket
        import platform
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        print(f"[{tag}] DEBUG: TELEGRAM_BOT_TOKEN={bot_token}")
        print(f"[{tag}] DEBUG: TELEGRAM_CHAT_ID={chat_id}")
        # Skip if not configured
        if not bot_token or not chat_id:
            print(f"[{tag}] Telegram not configured - skipping notification")
            return
        
        # Set timestamp to current time in IST (UTC+5:30)
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        timestamp = now_ist.strftime("%Y-%m-%d %H:%M:%S")
        
        # System details removed
        
        # Create message
        if success:
            message = f"<b>🚀 {tag} Auto Login Success!</b>\n"
        else:
            message = f"<b>❌ {tag} Auto Login Failed!</b>\n"

        # Basic info (crisp, with icons)
        message += f"👤 <b>Account:</b> <code>{username}</code>\n"
        message += f"🔑 <b>Auth:</b> <code>{auth_code}</code>\n"
        message += f"⏰ <b>Time:</b> <code>{timestamp}</code>\n"

        # Login details
        message += "\n<b>🔐 Login</b>\n"
        if totp_code:
            message += f"• <b>TOTP:</b> <code>{totp_code}</code>\n"
        if duration:
            message += f"• <b>⏳ Duration:</b> <code>{duration:.1f}s</code>\n"
        message += f"• <b>🖥️ Browser:</b> <code>Headless</code>\n"
        if final_url:
            message += f"• <b>🔗 URL:</b> <code>{final_url.split('?')[0]}</code>\n"

        # System info removed
        
        # Send via Telegram Bot API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"[{tag}] ✓ Telegram notification sent!")
        else:
            print(f"[{tag}] Warning: Telegram notification failed - {response.status_code}")
    except Exception as e:
        print(f"[{tag}] Warning: Could not send Telegram notification - {e}")


class StockoOAuthLogin:
    def browser_login_flow(self, auth_code, manual_login=True):
        """
        Automate login using Selenium WebDriver, with option for manual login entry.
        If manual_login is False, uses credentials from environment variables.
        """
        import time
        login_start_time = time.time()
        captured_totp = None
        final_url = None
        login_url = f"{self.base_url}/auth/{auth_code}"
        totp_secret = os.getenv('STOCKO_TOTP_SECRET')
        username = os.getenv('STOCKO_USERNAME')
        password = os.getenv('STOCKO_PASSWORD')
        success_message = "success"

        options = webdriver.ChromeOptions()
        # Run headless in auto mode, visible in manual mode
        if not manual_login:
            options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 120)
        try:
            try:
                driver.get(login_url)

                if manual_login:
                    print("\n[PP450] ========================================")
                    print("[PP450] MANUAL MODE - Complete full login process")
                    print("[PP450] 1. Enter your Client ID (username)")
                    print("[PP450] 2. Enter your Password")
                    print("[PP450] 3. Enter your TOTP code when prompted")
                    print("[PP450] Script is monitoring - no interruptions")
                    print("[PP450] ========================================\n")
                    # Don't ask for intermediate input - just wait and monitor
                else:
                    # Automated login using credentials from env
                    print("[PP450] Running in AUTOMATED mode - Filling credentials automatically...")
                    try:
                        # Wait for and fill login_id field (Client ID) - CORRECT FIELD NAME
                        login_id_field = wait.until(EC.presence_of_element_located((By.NAME, "login_id")))
                        login_id_field.clear()
                        login_id_field.send_keys(username)
                        print(f"[PP450] ✓ Entered Client ID: {username}")

                        # Fill password field
                        password_field = driver.find_element(By.NAME, "password")
                        password_field.clear()
                        password_field.send_keys(password)
                        print(f"[PP450] ✓ Entered password")

                        # Wait a moment for form to be ready
                        time.sleep(0.5)

                        # Submit login form
                        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        submit_button.click()
                        print("[PP450] ✓ Login form submitted")
                        print("[PP450] ⏳ Waiting for TOTP page...")
                        time.sleep(2)  # Wait for TOTP page to load
                    except Exception as e:
                        print(f"[PP450] ERROR filling login form: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_notification(
                            "PP450", username, auth_code,
                            success=False
                        )
                        return None

                # After login form, wait for page changes
                print("[PP450] Monitoring page for completion...")

                # First, check for TOTP field and auto-fill if found
                print("[PP450] ⏳ Checking for TOTP field (2 seconds)...")
                time.sleep(2)  # Give TOTP page time to appear

                try:
                    # PP450 uses "totp" field for TOTP (or "answers[]" if that doesn't work)
                    totp_field = None
                    try:
                        totp_field = driver.find_element(By.CSS_SELECTOR, "input[name='answers[]']")
                    except:
                        try:
                            totp_field = driver.find_element(By.NAME, "totp")
                        except:
                            # Try alternate field name
                            totp_field = driver.find_element(By.NAME, "answers[]")
                    
                    print("[PP450] 📱 TOTP field found! Generating and entering code...")
                    totp_code = TOTP(totp_secret).now()
                    captured_totp = totp_code  # Capture for Telegram notification
                    totp_field.clear()
                    totp_field.send_keys(totp_code)
                    print(f"[PP450] ✓ TOTP code entered: {totp_code}")
                    time.sleep(1)  # Show TOTP code entry

                    # Find and click submit button
                    totp_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    totp_submit.click()
                    print("[PP450] ✓ TOTP form submitted")
                    print("[PP450] ⏳ Waiting for success page...")
                    
                    # Wait for success page after TOTP submission (up to 15 seconds)
                    success_found = False
                    invalid_totp_retries = 2
                    attempt = 0
                    while attempt < 15:
                        time.sleep(1)
                        attempt += 1
                        try:
                            current_url = driver.current_url
                            page_text = driver.find_element(By.TAG_NAME, "body").text
                            page_text_lower = page_text.lower()
                            page_title_lower = (driver.title or "").lower()
                            url_lower = (current_url or "").lower()

                            if "invalid totp" in page_text_lower and invalid_totp_retries > 0:
                                invalid_totp_retries -= 1
                                print(f"[PP450] ⚠️  Invalid TOTP detected. Retrying... ({invalid_totp_retries} retries left)")
                                time.sleep(30)
                                try:
                                    totp_field = driver.find_element(By.CSS_SELECTOR, "input[name='answers[]']")
                                    totp_code = TOTP(totp_secret).now()
                                    captured_totp = totp_code
                                    totp_field.clear()
                                    totp_field.send_keys(totp_code)
                                    totp_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                                    totp_submit.click()
                                    print(f"[PP450] ✓ Retried TOTP code: {totp_code}")
                                    attempt = 0
                                    continue
                                except Exception as retry_error:
                                    print(f"[PP450] Retry submit failed: {retry_error}")

                            if (
                                "success" in page_text_lower
                                or "token generated successfully" in page_text_lower
                                or "success" in page_title_lower
                                or "token generated successfully" in page_title_lower
                                or "success" in url_lower
                            ):
                                success_found = True
                                final_url = current_url
                                print("[PP450] ✓ Success page found!")
                                break
                        except Exception as e:
                            print(f"[PP450] Error monitoring success: {e}")

                    if not success_found:
                        print("[PP450] ❌ Success page NOT found within 15 seconds after TOTP submission!")
                        send_telegram_notification(
                            "PP450", username, auth_code,
                            success=False
                        )
                        return False

                    # Calculate duration
                    duration = time.time() - login_start_time

                    print("\n" + "="*60)
                    print("[PP450] ✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
                    print("[PP450] Full authentication process completed!")
                    print("="*60 + "\n")

                    # Send Telegram notification with all details
                    send_telegram_notification(
                        "PP450",
                        username,
                        auth_code,
                        totp_code=captured_totp,
                        final_url=final_url,
                        duration=duration,
                        success=True
                    )

                    if self.auto_mode:
                        print("[PP450] Auto mode - closing browser automatically...")
                        return True
                    else:
                        input("[PP450] Press Enter to confirm and close browser...")
                        return True
                except Exception as e:
                    print(f"[PP450] Error during TOTP submission: {type(e).__name__} - {e}")
                    send_telegram_notification(
                        "PP450", username, auth_code,
                        success=False
                    )
                    return False
                    return True
            except Exception as e:
                import traceback
                print(f"[PP450] UNEXPECTED ERROR: {e}")
                traceback.print_exc()
                send_telegram_notification(
                    "PP450", username if 'username' in locals() else 'N/A', auth_code if 'auth_code' in locals() else 'N/A',
                    success=False
                )
                return False
        finally:
            driver.quit()

    def __init__(self, auto_mode=False):
        self.base_url = "https://sasstocko.broker.tradetron.tech"
        self.tag = "PP450"
        self.session = requests.Session()
        self.config_file = Path(__file__).parent / "config_pp450.json"
        self.auto_mode = auto_mode

    def load_credentials(self):
        """Load saved credentials from config file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def save_credentials(self, username):
        """Save username to config file (not password for security)"""
        config = {"username": username, "tag": self.tag}
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_totp_code(self):
        """Generate TOTP code from secret or get from user"""
        totp_secret = os.getenv('STOCKO_TOTP_SECRET')
        if totp_secret:
            code = TOTP(totp_secret).now()
            print(f"[PP450] Generated TOTP code: {code}")
            return code
        elif self.auto_mode:
            print(f"[PP450] ERROR: Auto mode enabled but TOTP secret not found!")
            print(f"[PP450] Required: STOCKO_TOTP_SECRET")
            sys.exit(1)
        else:
            return input("\n[PP450] Enter TOTP code: ").strip()

    def get_credentials(self):
        """Get login credentials from environment variables or user input"""
        # Check for environment variables (automated mode)
        if self.auto_mode or os.getenv('STOCKO_USERNAME'):
            username = os.getenv('STOCKO_USERNAME')
            password = os.getenv('STOCKO_PASSWORD')
            if username and password:
                print(f"[PP450] Using credentials from environment variables")
                return username, password
            elif self.auto_mode:
                print(f"[PP450] ERROR: Auto mode enabled but credentials not found in environment!")
                print(f"[PP450] Required: STOCKO_USERNAME, STOCKO_PASSWORD")
                sys.exit(1)
        
        # Manual mode - get from user
        config = self.load_credentials()
        
        if 'username' in config:
            username = config['username']
            print(f"Using saved username: {username}")
            use_saved = input("Use this username? (y/n): ").lower()
            if use_saved != 'y':
                username = input("Enter username/email: ")
        else:
            username = input("Enter username/email: ")
        
        password = getpass.getpass("Enter password: ")
        
        save = input("Save username for next time? (y/n): ").lower()
        if save == 'y':
            self.save_credentials(username)
        
        return username, password
    
    def handle_login_challenge(self, auth_code):
        """
        Handle the broker authentication flow - PP450
        """
        print(f"\n[PP450] Processing auth code: {auth_code}")
        
        # Step 1: Get auth page
        auth_url = f"{self.base_url}/auth/{auth_code}"
        
        try:
            print("[PP450] Fetching authentication page...")
            response = self.session.get(auth_url)
            response.raise_for_status()
            
            # Get credentials
            username, password = self.get_credentials()
            
            # Step 2: Submit login credentials
            print("[PP450] Submitting credentials...")
            login_data = {
                "username": username,
                "password": password
            }
            
            # Submit credentials
            login_response = self.session.post(
                auth_url,
                data=login_data,
                allow_redirects=False
            )
            
            # Check if TOTP is required
            if login_response.status_code in [200, 302, 303]:
                # Step 3: Handle TOTP (2FA)
                totp_code = self.get_totp_code()
                print("[PP450] Submitting TOTP code...")
                
                totp_data = {
                    "totp": totp_code
                }
                
                # Submit TOTP
                accept_response = self.session.post(
                    auth_url,
                    data=totp_data,
                    allow_redirects=False
                )
            else:
                accept_response = login_response
            
            # Check for redirect or success
            if accept_response.status_code in [200, 302, 303]:
                print("[PP450] Login successful!")
                
                # Check for redirect URL
                if 'Location' in accept_response.headers:
                    redirect_url = accept_response.headers['Location']
                    print(f"[PP450] Redirect URL: {redirect_url}")
                    
                    # Follow redirect to complete OAuth flow
                    final_response = self.session.get(redirect_url)
                    print(f"[PP450] Final status: {final_response.status_code}")
                    
                    return final_response
                else:
                    print("[PP450] Response:")
                    print(accept_response.text[:500])
                    return accept_response
            else:
                print(f"[PP450] Login failed with status: {accept_response.status_code}")
                print(f"[PP450] Response: {accept_response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[PP450] Error during login: {e}")
            return None
    
    def extract_tokens(self, response):
        """Extract access tokens from response"""
        try:
            # Try to parse JSON response
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                if 'access_token' in data:
                    print(f"\n[PP450] Access Token: {data['access_token']}")
                if 'refresh_token' in data:
                    print(f"[PP450] Refresh Token: {data['refresh_token']}")
                return data
            
            # Check for tokens in URL (redirect case)
            if response.url and ('access_token' in response.url or 'code' in response.url):
                parsed = urlparse(response.url)
                params = parse_qs(parsed.fragment or parsed.query)
                print(f"\n[PP450] Tokens found in URL:")
                for key, value in params.items():
                    print(f"  {key}: {value[0]}")
                return params
        except Exception as e:
            print(f"[PP450] Error extracting tokens: {e}")
        
        return None

def main():
    print("=" * 60)
    print("Stocko Broker Auto Login - PP450")
    print("=" * 60)
    

    # Check if running in automated mode
    auto_mode = os.getenv('STOCKO_AUTO_MODE', 'false').lower() == 'true'
    auth_code = os.getenv('STOCKO_AUTH_CODE')
    if not auth_code:
        print("[PP450] ERROR: STOCKO_AUTH_CODE not set in environment or .env.PP450")
        import sys
        sys.exit(1)
    if auto_mode:
        print("[PP450] Running in AUTOMATED mode (scheduled for 3 PM IST)")
    else:
        print("[PP450] Running in MANUAL mode")
    print(f"[PP450] Using auth code: {auth_code}")

    # Initialize login handler
    oauth = StockoOAuthLogin(auto_mode=auto_mode)

    # Use Selenium browser automation for login
    # In auto mode: manual_login=False (automated), In manual mode: manual_login=True (user enters creds)
    manual_login = not auto_mode
    result = oauth.browser_login_flow(auth_code, manual_login=manual_login)

if __name__ == "__main__":
    main()
