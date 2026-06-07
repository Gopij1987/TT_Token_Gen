"""
Token V1 - Multi-Account Stocko Login Automation
Extensible token generation for GJ114, PP450, RR1001 (and future accounts)
Usage:
    python token_automation.py --account GJ114
    python token_automation.py --account all
"""

import os
import sys
import time
import json
import traceback
import requests
import gc
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ── Configuration ─────────────────────────────────────────────────────────────
ACCOUNTS = {
    "GJ114": {"env_file": ".env.GJ114", "auth_code_env": "GJ114_AUTH_CODE"},
    "PP450": {"env_file": ".env.PP450", "auth_code_env": "PP450_AUTH_CODE"},
    "RR1001": {"env_file": ".env.RR1001", "auth_code_env": "RR1001_AUTH_CODE"},
    # Add new accounts here easily
}

BASE_URL = "https://sasstocko.broker.tradetron.tech"

# ── Telegram ─────────────────────────────────────────────────────────────────
def get_ram_usage():
    """Get current process RAM usage in MB"""
    if psutil:
        try:
            process = psutil.Process(os.getpid())
            ram_mb = process.memory_info().rss / 1024 / 1024
            return f"{ram_mb:.1f}MB"
        except Exception:
            pass
    return "N/A"

def send_telegram_notification(account_tag, success, details="", totp_code="", ram_usage=None):
    """Send Telegram notification for login result with RAM usage"""
    if ram_usage is None:
        ram_usage = get_ram_usage()
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if not bot_token or not chat_id:
                print(f"  Telegram not configured")
                return False
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = os.getenv(f"{account_tag}_USERNAME", account_tag)
            auth_code = os.getenv(f"{account_tag}_AUTH_CODE", "Unknown")
            
            if success:
                message = f"<b>✅ {account_tag} Token Generated</b>\n\n"
                message += f"👤 Account: <code>{username}</code>\n"
                message += f"🔑 Auth Code: <code>{auth_code}</code>\n"
                message += f"⏰ Time: <code>{timestamp}</code>\n"
                message += f"💾 RAM: <code>{ram_usage}</code>\n"
                if totp_code:
                    message += f"🔐 TOTP: <code>{totp_code}</code>\n"
                if details:
                    message += f"\n📋 {details}"
            else:
                message = f"<b>❌ {account_tag} Token Failed</b>\n\n"
                message += f"👤 Account: <code>{username}</code>\n"
                message += f"🔑 Auth Code: <code>{auth_code}</code>\n"
                message += f"⏰ Time: <code>{timestamp}</code>\n"
                message += f"💾 RAM: <code>{ram_usage}</code>\n"
                if details:
                    message += f"\n⚠️ Error: {details}"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"  Telegram notification sent ({'success' if success else 'error'})")
                return True
            else:
                print(f"  Telegram notification failed: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return False
        except requests.exceptions.Timeout:
            print(f"  Telegram timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False
        except Exception as e:
            print(f"  Telegram error: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False
    return False

# ── Robust Field Finding ────────────────────────────────────────────────────
def find_field_robust(driver, selectors, timeout=10):
    """Try multiple selectors to find a field"""
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    for selector_type, selector_value in selectors:
        try:
            if selector_type == "name":
                return driver.find_element("name", selector_value)
            elif selector_type == "id":
                return driver.find_element("id", selector_value)
            elif selector_type == "css":
                return driver.find_element("css selector", selector_value)
            elif selector_type == "xpath":
                return driver.find_element("xpath", selector_value)
        except NoSuchElementException:
            continue
    raise NoSuchElementException(f"Could not find field with any selector: {selectors}")

def wait_for_field_robust(driver, selectors, timeout=30):
    """Wait for field using multiple selector strategies"""
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    
    wait = WebDriverWait(driver, timeout)
    for selector_type, selector_value in selectors:
        try:
            if selector_type == "name":
                return wait.until(EC.presence_of_element_located((By.NAME, selector_value)))
            elif selector_type == "id":
                return wait.until(EC.presence_of_element_located((By.ID, selector_value)))
            elif selector_type == "css":
                return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_value)))
        except TimeoutException:
            continue
    raise TimeoutException(f"Field not found with any selector: {selectors}")

# ── Login Flow ───────────────────────────────────────────────────────────────
def login_account(account_tag, auth_code):
    """Perform login for a single account"""
    print(f"\n{'='*60}")
    print(f"[{account_tag}] Starting login process...")
    print(f"{'='*60}")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from pyotp import TOTP
    except ImportError as e:
        error_msg = f"Required package not available: {e}"
        print(f"  ✗ {error_msg}")
        send_telegram_notification(account_tag, False, error_msg)
        return {"success": False, "error": error_msg}
    
    # Get credentials from environment
    username = os.getenv(f"{account_tag}_USERNAME")
    password = os.getenv(f"{account_tag}_PASSWORD")
    totp_secret = os.getenv(f"{account_tag}_TOTP_SECRET")
    
    if not all([username, password, totp_secret, auth_code]):
        error_msg = "Missing credentials in environment"
        print(f"  ✗ {error_msg}")
        send_telegram_notification(account_tag, False, error_msg)
        return {"success": False, "error": error_msg}
    
    # Setup Chrome with VPS memory optimization
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    # VPS memory optimization flags
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-features=site-per-process')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-blink-features=AutomationControlled')
    # Disable cache to reduce memory
    options.add_argument('--aggressive-cache-discard')
    options.add_argument('--disable-cache')
    options.add_argument('--disk-cache-size=0')
    # Enable memory saver (Chrome 110+)
    options.add_argument('--enable-features=MemorySaver')
    # Limit renderer processes
    options.add_argument('--renderer-process-limit=1')
    options.add_argument('--force-device-scale-factor=1')
    
    driver = None
    start_time = time.time()
    totp_code_used = ""
    
    try:
        print(f"  Launching Chrome...")
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(10)
        except Exception as chrome_err:
            error_msg = f"Chrome launch failed: {str(chrome_err)}"
            print(f"  ✗ {error_msg}")
            send_telegram_notification(account_tag, False, error_msg)
            return {"success": False, "error": error_msg}
        wait = WebDriverWait(driver, 30)
        
        # Navigate to login page
        login_url = f"{BASE_URL}/auth/{auth_code}"
        driver.get(login_url)
        print(f"  ✓ Loaded login page")
        
        # Find and fill username
        username_selectors = [
            ("name", "login_id"), ("name", "username"),
            ("id", "username"), ("id", "login_id"),
            ("css", "input[name*='login' i]"), ("css", "input[name*='user' i]"),
            ("css", "input[type='text']:first-of-type"),
        ]
        try:
            login_field = wait_for_field_robust(driver, username_selectors)
        except Exception as e:
            raise Exception(f"Username field not found: {e}")
        
        login_field.clear()
        login_field.send_keys(username)
        print(f"  ✓ Username entered: {username}")
        
        # Find and fill password
        password_selectors = [
            ("name", "password"), ("id", "password"),
            ("css", "input[type='password']"), ("css", "input[name*='pass' i]"),
        ]
        try:
            password_field = find_field_robust(driver, password_selectors)
        except Exception as e:
            raise Exception(f"Password field not found: {e}")
        
        password_field.clear()
        password_field.send_keys(password)
        print(f"  ✓ Password entered")
        
        # Find and click submit
        submit_selectors = [
            ("css", "button[type='submit']"), ("css", "input[type='submit']"),
            ("xpath", "//button[contains(text(), 'Submit') or contains(text(), 'Login')]"),
            ("css", "button"),
        ]
        try:
            submit_btn = find_field_robust(driver, submit_selectors)
        except Exception as e:
            raise Exception(f"Submit button not found: {e}")
        
        submit_btn.click()
        print(f"  ✓ Login submitted")
        
        # Wait for TOTP page
        time.sleep(2)
        
        # Check for errors
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "invalid" in page_text and ("credentials" in page_text or "username" in page_text or "password" in page_text):
            raise Exception("Invalid username or password")
        
        # Find and fill TOTP
        totp_selectors = [
            ("id", "totp_input"), ("name", "totp"), ("name", "answers[]"),
            ("css", "input[id*='totp' i]"), ("css", "input[name*='totp' i]"),
            ("css", "input[name*='answer' i]"), ("css", "input[type='password']:first-of-type"),
        ]
        try:
            totp_field = find_field_robust(driver, totp_selectors)
        except Exception as e:
            raise Exception(f"TOTP field not found: {e}")
        
        totp_code = TOTP(totp_secret).now()
        totp_code_used = totp_code
        totp_field.clear()
        totp_field.send_keys(totp_code)
        print(f"  ✓ TOTP entered: {totp_code}")
        
        # Submit TOTP
        totp_submit_selectors = [
            ("css", "button[type='submit']"), ("css", "input[type='submit']"),
            ("xpath", "//button[contains(text(), 'Submit') or contains(text(), 'Verify')]"),
            ("css", "button"),
        ]
        try:
            totp_submit = find_field_robust(driver, totp_submit_selectors)
            totp_submit.click()
        except Exception as e:
            raise Exception(f"TOTP submit button not found: {e}")
        
        print(f"  ✓ TOTP submitted")
        time.sleep(3)
        
        # Check result
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        current_url = driver.current_url
        
        if "invalid" in page_text and ("totp" in page_text or "code" in page_text):
            raise Exception("Invalid TOTP code - check TOTP secret or clock sync")
        
        if "success" in page_text or "approved" in page_text:
            duration = time.time() - start_time
            ram_usage = get_ram_usage()
            details = f"Duration: {duration:.1f}s, RAM: {ram_usage}"
            print(f"  ✓✓✓ LOGIN SUCCESSFUL! ({duration:.1f}s, RAM: {ram_usage})")
            send_telegram_notification(account_tag, True, details, totp_code_used, ram_usage)
            return {"success": True, "duration": duration, "totp": totp_code_used}
        
        if "sasstocko.broker.tradetron.tech" not in current_url or "success" in current_url:
            duration = time.time() - start_time
            ram_usage = get_ram_usage()
            details = f"Redirected, Duration: {duration:.1f}s, RAM: {ram_usage}"
            print(f"  ✓✓✓ LOGIN SUCCESSFUL! (redirect, {duration:.1f}s, RAM: {ram_usage})")
            send_telegram_notification(account_tag, True, details, totp_code_used, ram_usage)
            return {"success": True, "duration": duration, "totp": totp_code_used}
        
        raise Exception("Unclear login result - no success message or redirect")
        
    except Exception as e:
        duration = time.time() - start_time
        ram_usage = get_ram_usage()
        error_msg = f"{str(e)} (after {duration:.1f}s)"
        print(f"  ✗ LOGIN FAILED: {error_msg}")
        print(f"  💾 RAM used: {ram_usage}")
        send_telegram_notification(account_tag, False, error_msg, totp_code_used, ram_usage)
        return {"success": False, "error": str(e), "duration": duration}
    
    finally:
        if driver:
            try:
                # Clean up before quitting
                try:
                    driver.delete_all_cookies()
                except Exception:
                    pass
                try:
                    driver.close()
                except Exception:
                    pass
                driver.quit()
                print(f"  ✓ Browser closed")
            except Exception as cleanup_err:
                print(f"  ⚠ Browser cleanup warning: {cleanup_err}")
            finally:
                # Force garbage collection
                del driver
                gc.collect()
                time.sleep(0.5)
                print(f"  ✓ Cleanup complete")

# ── Main ──────────────────────────────────────────────────────────────────────
def run_token_automation(account_tag):
    """Run token generation for single account"""
    # Load account-specific .env file
    token_v1_path = Path(__file__).parent
    account_config = ACCOUNTS.get(account_tag)
    
    if not account_config:
        return {"success": False, "error": f"Unknown account: {account_tag}"}
    
    env_file = token_v1_path / account_config["env_file"]
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)
        print(f"Loaded environment from {env_file}")
    else:
        # Try parent directory (essential folder)
        env_file = token_v1_path.parent / "essential" / account_config["env_file"]
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)
            print(f"Loaded environment from {env_file}")
        else:
            print(f"Warning: {account_config['env_file']} not found, using current environment")
    
    # Get auth code
    auth_code = os.getenv(account_config["auth_code_env"])
    if not auth_code:
        return {"success": False, "error": f"Auth code not found: {account_config['auth_code_env']}"}
    
    # Run login
    return login_account(account_tag, auth_code)

def run_all_accounts():
    """Run token generation for all configured accounts"""
    results = {}
    print(f"\n{'#'*70}")
    print(f"# TOKEN V1 - Running all {len(ACCOUNTS)} accounts")
    print(f"{'#'*70}")
    
    for account_tag in ACCOUNTS:
        result = run_token_automation(account_tag)
        results[account_tag] = result
        # Force garbage collection between accounts
        gc.collect()
        time.sleep(3)  # Delay between accounts for OS cleanup
    
    # Summary
    success_count = sum(1 for r in results.values() if r.get("success"))
    print(f"\n{'='*70}")
    print(f"SUMMARY: {success_count}/{len(ACCOUNTS)} accounts successful")
    print(f"{'='*70}")
    
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Token V1 - Stocko Login Automation")
    parser.add_argument("--account", required=True, help="Account tag (e.g., GJ114, PP450, RR1001) or 'all'")
    args = parser.parse_args()
    
    if args.account.lower() == "all":
        results = run_all_accounts()
        # Exit with error code if any failed
        success = all(r.get("success") for r in results.values())
        sys.exit(0 if success else 1)
    else:
        result = run_token_automation(args.account)
        sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()
