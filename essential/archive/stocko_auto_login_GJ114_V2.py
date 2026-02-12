"""
Stocko Broker Auto Login Script - GJ114 V2
Enhanced with credential validation & TOTP error detection
Automates the OAuth authentication flow for Stocko via Tradetron
Tag: GJ114
Supports: Manual mode & Automated mode (with env variables)
"""
import os
import sys
import json
import time
import requests
import traceback
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
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
dotenv_path = Path(__file__).parent / '.env.GJ114'
load_dotenv(dotenv_path)


def send_telegram_notification(tag, username, auth_code, totp_code=None, final_url=None, duration=None, success=True, last_update_time=None):
    """Send Telegram notification for login with detailed information"""
    try:
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
            print(f"[{self.tag}] Generated TOTP code: {code}")
            return code
        elif self.auto_mode:
            print(f"[{self.tag}] ERROR: Auto mode enabled but TOTP secret not found!")
            print(f"[{self.tag}] Required: STOCKO_TOTP_SECRET")
            sys.exit(1)
        else:
            return input(f"\n[{self.tag}] Enter TOTP code: ").strip()

    def browser_login_flow(self, auth_code, manual_login=True):
        """
        Automate login using Selenium WebDriver with enhanced error detection.
        
        Step 1: Load login page
        Step 2: Fill credentials & detect if page navigates or shows error
        Step 3-4: Detect TOTP field & fill it
        Step 5: After TOTP submit, detect if page navigates or shows error
        Step 6: Wait for success page
        """
        
        # Track start time for duration
        start_time = time.time()
        captured_totp = None
        final_url = None
        login_url = f"{self.base_url}/auth/{auth_code}"
        totp_secret = os.getenv('STOCKO_TOTP_SECRET')
        username = os.getenv('STOCKO_USERNAME')
        password = os.getenv('STOCKO_PASSWORD')

        options = webdriver.ChromeOptions()
        # Show browser window for progress monitoring (remove headless for debugging)
        # To run headless, uncomment the line below:
        # options.add_argument('--headless=new')
        
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 120)
        
        try:
            login_start_time = time.time()
            
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Loading login page
            # ═══════════════════════════════════════════════════════════
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
                print("[GJ114] MANUAL MODE: Please enter credentials manually in browser")
                print("[GJ114] Script will monitor for page changes...")
                print("[GJ114] ════════════════════════════════════════════════════════════")
            else:
                # ═══════════════════════════════════════════════════════════
                # STEP 2: Fill credentials & detect page transition or error
                # ═══════════════════════════════════════════════════════════
                print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] STEP 2: AUTO MODE - Filling credentials...")
                print("[GJ114] ═══════════════════════════════════════════════════════════")
                
                try:
                    # Find and fill login fields
                    print("[GJ114] Finding login fields...")
                    login_id_field = wait.until(EC.presence_of_element_located((By.NAME, "login_id")))
                    password_field = driver.find_element(By.NAME, "password")
                    
                    print(f"[GJ114] Entering username: {username}")
                    login_id_field.clear()
                    login_id_field.send_keys(username)
                    
                    print("[GJ114] Entering password...")
                    password_field.clear()
                    password_field.send_keys(password)
                    
                    # Click submit
                    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    submit_button.click()
                    print("[GJ114] ✓ Login form submitted")
                    print("[GJ114] ⏳ Waiting for page transition...")
                    
                    # ═══════════════════════════════════════════════════════════
                    # CRITICAL: Check if page navigated or shows error
                    # ═══════════════════════════════════════════════════════════
                    print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                    print("[GJ114] CHECKING: Page transition or error?")
                    print("[GJ114] ═══════════════════════════════════════════════════════════")
                    
                    initial_login_url = driver.current_url
                    
                    try:
                        # Wait for URL to change (TOTP page) - instant detection
                        wait.until(EC.url_changes(initial_login_url), timeout=10)
                        print(f"[GJ114] ✅ PAGE TRANSITIONED TO TOTP!")
                        print(f"[GJ114]    New URL: {driver.current_url[:70]}...")
                    except TimeoutException:
                        # URL didn't change, check for login error
                        print("[GJ114] URL did not change - checking for login error...")
                        try:
                            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                            if "error" in page_text or "invalid" in page_text or "failed" in page_text:
                                print("[GJ114] ❌ LOGIN ERROR detected")
                                send_telegram_notification(
                                    "GJ114", username, auth_code,
                                    success=False,
                                    final_url=driver.current_url,
                                    duration=None
                                )
                                return False
                            else:
                                print("[GJ114] ⚠️  No error detected, continuing...")
                        except:
                            print("[GJ114] ⚠️  Could not read page, continuing...")
                
                except Exception as e:
                    print(f"[GJ114] ❌ Error during credential entry: {e}")
                    traceback.print_exc()
                    send_telegram_notification(
                        "GJ114", username, auth_code,
                        success=False
                    )
                    return False

            # ═══════════════════════════════════════════════════════════
            # STEP 3-4: Detect TOTP field & fill it
            # ═══════════════════════════════════════════════════════════
            print("\n[GJ114] ═══════════════════════════════════════════════════════════")
            print("[GJ114] STEP 3-4: Checking for TOTP field...")
            print("[GJ114] ═══════════════════════════════════════════════════════════")
            print("[GJ114] Scanning for TOTP field (up to 15 seconds)...\n")
            
            totp_field = None
            for attempt in range(15):
                try:
                    totp_field = driver.find_element(By.NAME, "answers[]")
                    print(f"[GJ114] ✅ TOTP field found on attempt {attempt + 1}!")
                    break
                except:
                    if attempt % 3 == 0:
                        print(f"[GJ114] Attempt {attempt + 1}/15 - TOTP field not yet visible...")
                    time.sleep(1)
            
            if totp_field is None:
                print("[GJ114] ❌ TOTP field NOT found after 15 seconds")
                print("[GJ114] Displaying page content for debugging...")
                page_elements = driver.find_elements(By.CSS_SELECTOR, "input")
                print(f"[GJ114] Found {len(page_elements)} input fields:")
                for idx, elem in enumerate(page_elements[:10]):
                    print(f"  {idx+1}. Name: {elem.get_attribute('name')}, Type: {elem.get_attribute('type')}, ID: {elem.get_attribute('id')}")
                
                if manual_login:
                    print("[GJ114] ⏳ Waiting for manual TOTP entry (manual mode)...")
                    print("[GJ114] Please enter TOTP code manually in the browser")
                else:
                    print("[GJ114] ❌ Auto mode requires TOTP field to be visible")
                    send_telegram_notification(
                        "GJ114", username, auth_code,
                        success=False
                    )
                    return False
            else:
                # ═══════════════════════════════════════════════════════════
                # TOTP field found - enter code & monitor for errors
                # ═══════════════════════════════════════════════════════════
                print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                print("[GJ114] STEP 5: TOTP field found - Entering code...")
                print("[GJ114] ═══════════════════════════════════════════════════════════")
                
                invalid_totp_retries = 2
                totp_attempt = 0
                
                while totp_attempt <= invalid_totp_retries:
                    try:
                        # Generate TOTP code
                        captured_totp = self.get_totp_code()
                        print(f"[GJ114] Generated TOTP: {captured_totp}")
                        
                        # Clear and enter TOTP
                        totp_field = driver.find_element(By.NAME, "answers[]")
                        totp_field.clear()
                        totp_field.send_keys(captured_totp)
                        print(f"[GJ114] ✓ Entered TOTP code: {captured_totp}")
                        time.sleep(1)
                        
                        # Find and click TOTP submit button
                        totp_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                        print("[GJ114] ✓ Clicking TOTP submit button...")
                        totp_submit.click()
                        print("[GJ114] ⏳ TOTP submitted - waiting for redirect...")
                        
                        # ═══════════════════════════════════════════════════════════
                        # CRITICAL: Wait for URL to change (instant detection)
                        # ═══════════════════════════════════════════════════════════
                        print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                        print("[GJ114] CHECKING: Page redirecting or error?")
                        print("[GJ114] ═══════════════════════════════════════════════════════════")
                        
                        totp_page_changed = False
                        totp_error_detected = False
                        initial_totp_url = driver.current_url
                        
                        try:
                            # Use explicit wait for URL change - instant detection, no polling!
                            wait.until(EC.url_changes(initial_totp_url), timeout=30)
                            totp_page_changed = True
                            new_url = driver.current_url
                            print(f"[GJ114] ✅ PAGE REDIRECTED INSTANTLY!")
                            print(f"[GJ114]    New URL: {new_url[:70]}...")
                            break  # Exit TOTP retry loop - success!
                        except TimeoutException:
                            # URL didn't change, check for errors
                            print("[GJ114] No redirect detected - checking for error...")
                            try:
                                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                                if "invalid" in page_text or "error" in page_text or "expired" in page_text:
                                    totp_error_detected = True
                                    print(f"[GJ114] ❌ TOTP ERROR detected on page")
                                else:
                                    print("[GJ114] ⚠️  No error found - assuming success")
                                    totp_page_changed = True
                                    break
                            except:
                                print("[GJ114] ⚠️  Unable to read page - assuming success")
                                totp_page_changed = True
                                break
                        
                        # Decide what happened after TOTP submission
                        print("\n[GJ114] ═══════════════════════════════════════════════════════════")
                        print("[GJ114] RESULT OF TOTP SUBMISSION:")
                        print("[GJ114] ═══════════════════════════════════════════════════════════")
                        
                        if totp_error_detected:
                            print(f"[GJ114] ❌ TOTP ERROR detected")
                            # Retry logic for invalid TOTP
                            if totp_attempt < invalid_totp_retries:
                                print(f"[GJ114] ⏳ Retrying TOTP (Attempt {totp_attempt + 1}/{invalid_totp_retries})...")
                                print(f"[GJ114] Waiting 30 seconds for new time window...")
                                time.sleep(30)  # Wait for new TOTP window
                                totp_attempt += 1
                                continue
                            else:
                                print("[GJ114] ❌ No retries left - TOTP failed")
                                send_telegram_notification(
                                    "GJ114", username, auth_code,
                                    totp_code=captured_totp,
                                    success=False,
                                    final_url=driver.current_url,
                                    duration=None
                                )
                                return False
                        
                        elif totp_page_changed:
                            print("[GJ114] ✅ PAGE REDIRECTED - TOTP accepted!")
                            time.sleep(1)  # Brief wait for page load
                            break  # Exit TOTP retry loop - success!
                    
                    except Exception as e:
                        print(f"[GJ114] ❌ ERROR during TOTP entry/submission: {e}")
                        traceback.print_exc()
                        send_telegram_notification(
                            "GJ114", username, auth_code,
                            success=False
                        )
                        return False

            # ═══════════════════════════════════════════════════════════
            # STEP 6: Wait for success page
            # ═══════════════════════════════════════════════════════════
            print("\n[GJ114] ═══════════════════════════════════════════════════════════")
            print("[GJ114] STEP 6: Waiting for success page...")
            print("[GJ114] ═══════════════════════════════════════════════════════════")
            
            try:
                # Wait for success URL or success text (30 seconds max)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")), timeout=30)
                time.sleep(2)
                
                current_url = driver.current_url
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                
                if "success" in page_text or "success" in current_url.lower():
                    print("[GJ114] ✅ SUCCESS PAGE DETECTED!")
                    success_found = True
                else:
                    print("[GJ114] ❌ Success page not found")
                    success_found = False
                    
            except Exception as e:
                print(f"[GJ114] ❌ Error waiting for success page: {e}")
                success_found = False
            
            if not success_found:
                print("[GJ114] ❌ Login did not complete successfully")
                send_telegram_notification(
                    "GJ114", username, auth_code,
                    success=False,
                    final_url=driver.current_url,
                    duration=None
                )
                return False

            # ═══════════════════════════════════════════════════════════
            # LOGIN SUCCESSFUL!
            # ═══════════════════════════════════════════════════════════
            print("\n[GJ114] ═══════════════════════════════════════════════════════════")
            print("[GJ114] ✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
            print("[GJ114] ═══════════════════════════════════════════════════════════")
            
            final_url = driver.current_url
            duration = time.time() - login_start_time
            
            print(f"[GJ114] ✓ Final URL: {final_url}")
            print(f"[GJ114] ✓ Total Duration: {duration:.1f} seconds")
            if captured_totp:
                print(f"[GJ114] ✓ TOTP Used: {captured_totp}")

            # Send success Telegram notification
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


def main():
    print("=" * 60)
    print("Stocko Broker Auto Login - GJ114 V2")
    print("Enhanced with Credential & TOTP Error Detection")
    print("=" * 60)
    
    # Check if running in automated mode
    auto_mode = os.getenv('STOCKO_AUTO_MODE', 'false').lower() == 'true'
    auth_code = os.getenv('STOCKO_AUTH_CODE')
    
    if not auth_code:
        print("[GJ114] ERROR: STOCKO_AUTH_CODE not set in environment or .env.GJ114")
        sys.exit(1)
    
    if auto_mode:
        print("[GJ114] Running in AUTOMATED mode (headless browser)")
    else:
        print("[GJ114] Running in MANUAL mode (visible browser)")
    
    print(f"[GJ114] Using auth code: {auth_code}")
    print("=" * 60)
    
    oauth = StockoOAuthLogin(auto_mode=auto_mode)
    manual_login = not auto_mode
    result = oauth.browser_login_flow(auth_code, manual_login=manual_login)
    
    if result:
        print("\n[GJ114] ✅ SCRIPT COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n[GJ114] ❌ SCRIPT FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
