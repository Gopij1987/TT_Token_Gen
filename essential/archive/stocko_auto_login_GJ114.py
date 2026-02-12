"""
Stocko Broker Auto Login Script - GJ114
Automates the OAuth authentication flow for Stocko via Tradetron
Tag: GJ114
Supports: Manual mode & Automated mode (with env variables)
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
import getpass
import os
from pathlib import Path
from pyotp import TOTP
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# Load environment variables from absolute path
from pathlib import Path
dotenv_path = Path(__file__).parent / '.env.GJ114'
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
        # Track start time for duration
        import time
        start_time = time.time()
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
            import time
            login_start_time = time.time()
            try:
                print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] STEP 1: Loading login page...")
                print("[GJ114] ═══════════════════════════════════════════════════════════")
                driver.get(login_url)
                print(f"[GJ114] ✓ Login URL loaded: {login_url}")
                time.sleep(2)
                
                current_url = driver.current_url
                page_title = driver.title
                print(f"[GJ114] Current URL: {current_url}")
                print(f"[GJ114] Page Title: {page_title}")

                if manual_login:
                    print("\n[GJ114] ════════════════════════════════════════════════════════════")
                    print("[GJ114] MANUAL MODE - STEP 2: Auto-filling credentials from environment")
                    print("[GJ114] ════════════════════════════════════════════════════════════")
                    print(f"[GJ114] 1️⃣  Entering Client ID: {username}")
                    print("[GJ114] 2️⃣  Entering Password from env")
                    print("[GJ114] 3️⃣  Clicking Submit button")
                    print("[GJ114] 4️⃣  Script will monitor for TOTP page...")
                    print("[GJ114] ════════════════════════════════════════════════════════════\n")
                    try:
                        login_id_field = wait.until(EC.presence_of_element_located((By.NAME, "login_id")))
                        login_id_field.clear()
                        login_id_field.send_keys(username)
                        print(f"[GJ114] ✓ Entered Client ID: {username}")
                        time.sleep(1)
                        password_field = driver.find_element(By.NAME, "password")
                        password_field.clear()
                        password_field.send_keys(password)
                        print("[GJ114] ✓ Entered password")
                        time.sleep(2)  # Delay before submit
                        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        submit_button.click()
                        print("[GJ114] ✓ Login form submitted")
                        print("[GJ114] ⏳ Waiting for TOTP page...")
                        time.sleep(3)
                        # Check for login error after submission
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        page_text_lower = page_text.lower()
                        if "error" in page_text_lower or "invalid" in page_text_lower or "failed" in page_text_lower:
                            error_msg = page_text[:200]
                            print(f"[GJ114] ❌ Login error detected: {error_msg}")
                            send_telegram_notification(
                                "GJ114", username, auth_code,
                                success=False,
                                final_url=driver.current_url,
                                duration=None
                            )
                            return None
                    except Exception as e:
                        print(f"[GJ114] ERROR filling login form in manual mode: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_notification(
                            "GJ114", username, auth_code,
                            success=False
                        )
                        return None
                else:
                    # Automated login using credentials from env
                    print("[GJ114] Running in AUTOMATED mode - Filling credentials automatically...")
                    try:
                        # Wait for and fill login_id field (Client ID) - CORRECT FIELD NAME
                        login_id_field = wait.until(EC.presence_of_element_located((By.NAME, "login_id")))
                        login_id_field.clear()
                        login_id_field.send_keys(username)
                        print(f"[GJ114] ✓ Entered Client ID: {username}")
                        time.sleep(1)  # Pause so user can see

                        # Fill password field
                        password_field = driver.find_element(By.NAME, "password")
                        password_field.clear()
                        password_field.send_keys(password)
                        print(f"[GJ114] ✓ Entered password")
                        time.sleep(2)  # Delay before submit

                        # Submit login form
                        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        submit_button.click()
                        print("[GJ114] ✓ Login form submitted")
                        print("[GJ114] ⏳ Waiting for TOTP page...")
                        time.sleep(3)  # Wait for TOTP page to load - IMPORTANT
                        # Check for login error after submission
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        page_text_lower = page_text.lower()
                        if "error" in page_text_lower or "invalid" in page_text_lower or "failed" in page_text_lower:
                            error_msg = page_text[:200]
                            print(f"[GJ114] ❌ Login error detected: {error_msg}")
                            send_telegram_notification(
                                "GJ114", username, auth_code,
                                success=False,
                                final_url=driver.current_url,
                                duration=None
                            )
                            return None
                    except Exception as e:
                        print(f"[GJ114] ERROR filling login form: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_notification(
                            "GJ114", username, auth_code,
                            success=False
                        )
                        return None

                # After login form, monitor page changes
                print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] STEP 3: Monitoring page after login form submission...")
                print("[GJ114] ═══════════════════════════════════════════════════════════")

                # First, check for TOTP field and auto-fill if found
                print("[GJ114] Checking for TOTP field (scanning for up to 15 seconds)...\n")
                # Extra check for login errors after waiting for TOTP page
                page_text = driver.find_element(By.TAG_NAME, "body").text
                page_text_lower = page_text.lower()
                if "error" in page_text_lower or "invalid" in page_text_lower or "failed" in page_text_lower:
                    error_msg = page_text[:200]
                    print(f"[GJ114] ❌ Login error detected after form submit: {error_msg}")
                    send_telegram_notification(
                        "GJ114", username, auth_code,
                        success=False,
                        final_url=driver.current_url,
                        duration=None
                    )
                    return None
                
                # Wait for TOTP page to load - try multiple times with increasing wait
                totp_field = None
                login_retry_done = False
                for attempt in range(15):
                    time.sleep(1)
                    try:
                        current_url = driver.current_url
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        page_len = len(page_text)
                        page_text_lower = page_text.lower()
                        
                        print(f"[GJ114] Attempt {attempt + 1}/15 | URL: {current_url} | Page Text Length: {page_len}")

                        # Detect login error page and retry once in auto mode
                        if (
                            not manual_login
                            and not login_retry_done
                            and ("something went wrong" in page_text_lower or "retry" in page_text_lower)
                        ):
                            print("[GJ114] ⚠️  Login error detected. Retrying login once...")
                            login_retry_done = True
                            try:
                                driver.get(login_url)
                                time.sleep(1)
                                login_id_field = wait.until(EC.presence_of_element_located((By.NAME, "login_id")))
                                login_id_field.clear()
                                login_id_field.send_keys(username)
                                password_field = driver.find_element(By.NAME, "password")
                                password_field.clear()
                                password_field.send_keys(password)
                                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                                submit_button.click()
                                print("[GJ114] ✓ Login retried")
                                time.sleep(2)
                                continue
                            except Exception as retry_error:
                                print(f"[GJ114] Retry failed: {retry_error}")
                        
                        # Try different field selectors (matches inspected DOM)
                        try:
                            totp_field = driver.find_element(By.CSS_SELECTOR, "input[name='answers[]']")
                            print(f"[GJ114] ✅ FOUND: TOTP field input[name='answers[]'] at attempt {attempt + 1}!")
                            break
                        except:
                            try:
                                totp_field = driver.find_element(By.NAME, "answers[]")
                                print(f"[GJ114] ✅ FOUND: TOTP field 'answers[]' at attempt {attempt + 1}!")
                                break
                            except:
                                try:
                                    totp_field = driver.find_element(By.NAME, "totp")
                                    print(f"[GJ114] ✅ FOUND: TOTP field 'totp' at attempt {attempt + 1}!")
                                    break
                                except:
                                    try:
                                        totp_field = driver.find_element(By.ID, "totp")
                                        print(f"[GJ114] ✅ FOUND: TOTP field by ID at attempt {attempt + 1}!")
                                        break
                                    except:
                                        totp_field = None
                    except Exception as e:
                        print(f"[GJ114] Error during monitoring: {e}")
                
                if totp_field is None:
                    # Final check - what's on the page?
                    print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                    print("[GJ114] ❌ TOTP FIELD NOT FOUND - Diagnostic Information:")
                    print("[GJ114] ═══════════════════════════════════════════════════════════")
                    try:
                        current_url = driver.current_url
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        page_source = driver.page_source
                        
                        print(f"[GJ114] Current URL: {current_url}")
                        print(f"[GJ114] Page Title: {driver.title}")
                        print(f"[GJ114] Page Text Length: {len(page_text)}")
                        print(f"[GJ114] Page HTML Length: {len(page_source)}")
                        print(f"\n[GJ114] Page Content (First 500 chars):\n{page_text[:500]}")
                        print(f"\n[GJ114] All input fields found on page:")
                        
                        # List all input fields
                        all_inputs = driver.find_elements(By.TAG_NAME, "input")
                        for i, inp in enumerate(all_inputs):
                            inp_name = inp.get_attribute("name")
                            inp_id = inp.get_attribute("id")
                            inp_type = inp.get_attribute("type")
                            print(f"  Input {i+1}: name='{inp_name}' id='{inp_id}' type='{inp_type}'")
                        
                        print(f"\n[GJ114] All button fields found on page:")
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                        for i, btn in enumerate(all_buttons):
                            btn_name = btn.get_attribute("name")
                            btn_id = btn.get_attribute("id")
                            btn_text = btn.text
                            print(f"  Button {i+1}: name='{btn_name}' id='{btn_id}' text='{btn_text}'")
                    except Exception as e:
                        print(f"[GJ114] Error getting page info: {e}")
                    
                    print("\n[GJ114] ⚠️  TOTP field not found after 15 seconds")
                    print("[GJ114] Waiting for you to manually enter TOTP...\n")
                    input("[GJ114] ⏳ Press ENTER once you've entered TOTP and clicked submit...")
                    time.sleep(2)
                else:
                    # TOTP field found - enter code
                    print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                    print("[GJ114] STEP 4: TOTP field found - Entering code...")
                    print("[GJ114] ═══════════════════════════════════════════════════════════")
                    try:
                        time.sleep(2)  # Delay before entering TOTP
                        totp_code = TOTP(totp_secret).now()
                        captured_totp = totp_code
                        print(f"[GJ114] Generated TOTP code: {totp_code}")
                        totp_field.clear()
                        totp_field.send_keys(totp_code)
                        print(f"[GJ114] ✓ TOTP code entered in field")
                        time.sleep(1)
                        # Find and click submit button
                        totp_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        totp_submit.click()
                        print("[GJ114] ✓ TOTP form submitted")
                        time.sleep(3)
                        # Check for TOTP error after submission
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        page_text_lower = page_text.lower()
                        if "error" in page_text_lower or "invalid" in page_text_lower or "failed" in page_text_lower:
                            error_msg = page_text[:200]
                            print(f"[GJ114] ❌ TOTP error detected: {error_msg}")
                            send_telegram_notification(
                                "GJ114", username, auth_code,
                                totp_code=totp_code,
                                success=False,
                                final_url=driver.current_url,
                                duration=None
                            )
                            return False
                    except Exception as e:
                        print(f"[GJ114] Error entering TOTP: {type(e).__name__}: {e}")
                        send_telegram_notification(
                            "GJ114", username, auth_code,
                            success=False
                        )
                        return False

                # Wait for success page
                print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] STEP 5: Waiting for success page...")
                print("[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] Monitoring for success page (scanning for up to 20 seconds)...\n")
                
                success_found = False
                invalid_totp_retries = 2
                attempt = 0
                while attempt < 20:
                    time.sleep(1)
                    attempt += 1
                    try:
                        current_url = driver.current_url
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        page_text_lower = page_text.lower()
                        page_title_lower = (driver.title or "").lower()
                        url_lower = (current_url or "").lower()
                        
                        print(f"[GJ114] Attempt {attempt}/20 | URL: {current_url[:80]}...")

                        if "invalid totp" in page_text_lower and invalid_totp_retries > 0:
                            invalid_totp_retries -= 1
                            print(f"[GJ114] ⚠️  Invalid TOTP detected. Retrying... ({invalid_totp_retries} retries left)")
                            time.sleep(30)
                            try:
                                totp_field = driver.find_element(By.CSS_SELECTOR, "input[name='answers[]']")
                                totp_code = TOTP(totp_secret).now()
                                captured_totp = totp_code
                                totp_field.clear()
                                totp_field.send_keys(totp_code)
                                totp_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                                totp_submit.click()
                                print(f"[GJ114] ✓ Retried TOTP code: {totp_code}")
                                attempt = 0
                                continue
                            except Exception as retry_error:
                                print(f"[GJ114] Retry submit failed: {retry_error}")

                        if (
                            "success" in page_text_lower
                            or "token generated successfully" in page_text_lower
                            or "success" in page_title_lower
                            or "token generated successfully" in page_title_lower
                            or "success" in url_lower
                        ):
                            success_found = True
                            final_url = current_url
                            print(f"[GJ114] ✅ SUCCESS PAGE FOUND at attempt {attempt}!")
                            print(f"[GJ114] Page contains: '{page_text[:100]}'")
                            break
                    except Exception as e:
                        print(f"[GJ114] Error monitoring success: {e}")
                
                if not success_found:
                    print("\n[GJ114] ❌ SUCCESS PAGE NOT FOUND within 20 seconds")
                    print("[GJ114] Current page might still be loading...")
                    try:
                        page_text = driver.find_element(By.TAG_NAME, "body").text
                        print(f"[GJ114] Current page text: {page_text[:200]}")
                    except:
                        pass
                    send_telegram_notification(
                        "GJ114", username, auth_code,
                        success=False
                    )
                    return False

                # Success!
                print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] ✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
                print("[GJ114] ═══════════════════════════════════════════════════════════")
                final_url = driver.current_url
                duration = time.time() - login_start_time
                
                print(f"[GJ114] ✓ Final URL: {final_url}")
                print(f"[GJ114] ✓ Total Duration: {duration:.1f} seconds")
                if captured_totp:
                    print(f"[GJ114] ✓ TOTP Code Used: {captured_totp}")

                # Send Telegram notification
                send_telegram_notification(
                    "GJ114", 
                    username if 'username' in locals() else 'Manual',
                    auth_code, 
                    totp_code=captured_totp,
                    final_url=final_url,
                    duration=duration,
                    success=True
                )

                print("\n[GJ114] Closing browser in 3 seconds...")
                time.sleep(3)
                return True
                
            except Exception as e:
                import traceback
                print(f"\n[GJ114] ❌ UNEXPECTED ERROR: {e}")
                traceback.print_exc()
                send_telegram_notification(
                    "GJ114", username if 'username' in locals() else 'N/A', auth_code,
                    success=False
                )
                return False
        finally:
            driver.quit()
            print("[GJ114] Browser closed")

    def __init__(self, auto_mode=False):
        self.base_url = "https://sasstocko.broker.tradetron.tech"
        self.tag = "GJ114"
        self.session = requests.Session()
        self.config_file = Path(__file__).parent / "config_gj114.json"
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
            print(f"[GJ114] Generated TOTP code: {code}")
            return code
        elif self.auto_mode:
            print(f"[GJ114] ERROR: Auto mode enabled but TOTP secret not found!")
            print(f"[GJ114] Required: STOCKO_TOTP_SECRET")
            sys.exit(1)
        else:
            return input("\n[GJ114] Enter TOTP code: ").strip()

def main():
    print("=" * 60)
    print("Stocko Broker Auto Login - GJ114")
    print("=" * 60)
    

    # Check if running in automated mode
    auto_mode = os.getenv('STOCKO_AUTO_MODE', 'false').lower() == 'true'
    auth_code = os.getenv('STOCKO_AUTH_CODE')
    if not auth_code:
        print("[GJ114] ERROR: STOCKO_AUTH_CODE not set in environment or .env.GJ114")
        import sys
        sys.exit(1)
    if auto_mode:
        print("[GJ114] Running in AUTOMATED mode (scheduled for 3 PM IST)")
    else:
        print("[GJ114] Running in MANUAL mode")
    print(f"[GJ114] Using auth code: {auth_code}")
    oauth = StockoOAuthLogin(auto_mode=auto_mode)
    manual_login = not auto_mode
    result = oauth.browser_login_flow(auth_code, manual_login=manual_login)

if __name__ == "__main__":
    main()
