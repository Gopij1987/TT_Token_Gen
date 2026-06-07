"""
GJ114 Diagnostic & Validation Script
Comprehensive test to validate credentials, TOTP, and diagnose login issues
"""

import os
import sys
import re
import time
import socket
import platform
import requests
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


def log(message, level="INFO"):
    """Log with timestamp and level"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def check_env_file():
    """Phase 1: Check if .env.GJ114 exists and is readable"""
    log("\n[PHASE 1: Environment File Check]", "PHASE")
    env_paths = [
        Path(__file__).parent / ".env.GJ114",
        Path(__file__).parent.parent / "essential" / ".env.GJ114",
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            log(f"✓ Found .env.GJ114 at: {env_path}")
            return str(env_path)
    
    log("✗ .env.GJ114 not found in any location", "ERROR")
    return None


def validate_env_vars(env_path):
    """Phase 1: Validate all required environment variables"""
    log("\n[PHASE 1: Environment Variables Validation]", "PHASE")
    
    # Load the env file
    load_dotenv(env_path)
    
    required_vars = {
        "GJ114_USERNAME": r".+",
        "GJ114_PASSWORD": r".+",
        "GJ114_TOTP_SECRET": r"^[A-Z2-7=]+$",
        "GJ114_AUTH_CODE": r"^\d+$",
        "TELEGRAM_BOT_TOKEN": r"^\d+:[A-Za-z0-9_-]+$",
        "TELEGRAM_CHAT_ID": r"^-?\d+$"
    }
    
    results = {}
    all_valid = True
    
    for var_name, pattern in required_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            log(f"✗ {var_name}: NOT SET", "ERROR")
            results[var_name] = (False, "Not set")
            all_valid = False
            continue
        
        if re.match(pattern, value):
            # Mask sensitive data
            display_value = value
            if "PASSWORD" in var_name or "SECRET" in var_name or "TOKEN" in var_name:
                display_value = "****" + value[-4:] if len(value) > 4 else "****"
            log(f"✓ {var_name}: {display_value}")
            results[var_name] = (True, value)
        else:
            log(f"✗ {var_name}: INVALID FORMAT (expected: {pattern})", "ERROR")
            results[var_name] = (False, f"Invalid format")
            all_valid = False
    
    return all_valid, results


def validate_totp():
    """Phase 2: TOTP Diagnostics"""
    log("\n[PHASE 2: TOTP Diagnostics]", "PHASE")
    
    try:
        from pyotp import TOTP
        totp_secret = os.getenv("GJ114_TOTP_SECRET")
        
        if not totp_secret:
            log("✗ TOTP Secret not available for validation", "ERROR")
            return False, None
        
        # Generate TOTP
        totp = TOTP(totp_secret)
        current_code = totp.now()
        
        # Get time remaining
        time_remaining = 30 - (int(time.time()) % 30)
        
        log(f"✓ TOTP generates: {current_code}")
        log(f"  Time remaining: {time_remaining}s")
        
        if time_remaining < 10:
            log(f"⚠ WARNING: TOTP expires in {time_remaining}s - RISK of expiry during login!", "WARN")
            log(f"  Recommendation: Wait {time_remaining + 2}s for next window", "WARN")
        
        return True, {"code": current_code, "time_remaining": time_remaining}
    
    except Exception as e:
        log(f"✗ TOTP validation failed: {e}", "ERROR")
        return False, None


def check_dependencies():
    """Phase 1: Check required Python packages"""
    log("\n[PHASE 1: Dependencies Check]", "PHASE")
    
    required_packages = [
        "selenium",
        "pyotp",
        "python-dotenv",
        "requests"
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            if package == "python-dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            log(f"✓ {package}: Installed")
        except ImportError:
            log(f"✗ {package}: NOT INSTALLED (pip install {package})", "ERROR")
            all_installed = False
    
    return all_installed


def check_network():
    """Phase 3: Network Connectivity Tests"""
    log("\n[PHASE 3: Network Connectivity]", "PHASE")
    
    # Check internet connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        log("✓ Internet connectivity: OK")
    except OSError:
        log("✗ Internet connectivity: FAILED", "ERROR")
        return False
    
    # Check broker endpoint
    base_url = "https://sasstocko.broker.tradetron.tech"
    try:
        response = requests.get(base_url, timeout=10)
        log(f"✓ Broker endpoint reachable: {base_url}")
        log(f"  Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        log(f"✗ Broker endpoint unreachable: {e}", "ERROR")
        return False


def validate_telegram_config():
    """Phase 3: Validate Telegram Bot configuration (no message sent)"""
    log("\n[PHASE 3: Telegram Bot Configuration]", "PHASE")
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        log("✗ Telegram configuration incomplete", "ERROR")
        return False
    
    # Just validate format, don't send message yet
    log("✓ Telegram bot token format valid")
    log(f"✓ Telegram chat ID: {chat_id}")
    log("  (Notification will be sent after login completes)")
    return True


def send_telegram_notification(success, details=""):
    """Send Telegram notification after login attempt"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = os.getenv("GJ114_USERNAME", "Unknown")
    auth_code = os.getenv("GJ114_AUTH_CODE", "Unknown")
    
    if success:
        message = f"<b>✅ GJ114 Login SUCCESSFUL</b>\n\n"
        message += f"👤 Account: <code>{username}</code>\n"
        message += f"🔑 Auth Code: <code>{auth_code}</code>\n"
        message += f"⏰ Time: <code>{timestamp}</code>\n"
        if details:
            message += f"\n📋 {details}"
    else:
        message = f"<b>❌ GJ114 Login FAILED</b>\n\n"
        message += f"👤 Account: <code>{username}</code>\n"
        message += f"🔑 Auth Code: <code>{auth_code}</code>\n"
        message += f"⏰ Time: <code>{timestamp}</code>\n"
        if details:
            message += f"\n⚠️ Error: {details}"
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log(f"✓ Telegram notification sent ({'success' if success else 'error'})")
        else:
            log(f"✗ Telegram notification failed: HTTP {response.status_code}", "WARN")
    except Exception as e:
        log(f"✗ Failed to send Telegram notification: {e}", "WARN")


def test_login_live():
    """Phase 4: Live Login Test with Error Diagnosis"""
    log("\n[PHASE 4: Live Login Test]", "PHASE")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from pyotp import TOTP
    except ImportError as e:
        log(f"✗ Required package not available: {e}", "ERROR")
        return False, "import_error", str(e)
    
    # Get credentials
    username = os.getenv("GJ114_USERNAME")
    password = os.getenv("GJ114_PASSWORD")
    totp_secret = os.getenv("GJ114_TOTP_SECRET")
    auth_code = os.getenv("GJ114_AUTH_CODE")
    
    if not all([username, password, totp_secret, auth_code]):
        log("✗ Missing credentials for live test", "ERROR")
        return False, "missing_credentials", "Environment variables incomplete"
    
    # Setup Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    def find_field_robust(driver, selectors, timeout=10):
        """Try multiple selectors to find a field"""
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        for selector_type, selector_value in selectors:
            try:
                if selector_type == "name":
                    return driver.find_element(By.NAME, selector_value)
                elif selector_type == "id":
                    return driver.find_element(By.ID, selector_value)
                elif selector_type == "css":
                    return driver.find_element(By.CSS_SELECTOR, selector_value)
                elif selector_type == "xpath":
                    return driver.find_element(By.XPATH, selector_value)
            except NoSuchElementException:
                continue
        raise NoSuchElementException(f"Could not find field with any selector: {selectors}")
    
    def wait_for_field_robust(driver, selectors, timeout=30):
        """Wait for field using multiple selector strategies"""
        from selenium.common.exceptions import TimeoutException
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
    
    try:
        log("Launching Chrome (headless)...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 30)
        log("✓ Chrome launched")
        
        # Navigate to login page
        login_url = f"https://sasstocko.broker.tradetron.tech/auth/{auth_code}"
        driver.get(login_url)
        log(f"✓ Navigated to login page")
        
        # ROBUST: Try multiple selectors for username field
        log("Waiting for login form...")
        username_selectors = [
            ("name", "login_id"),
            ("name", "username"),
            ("id", "username"),
            ("id", "login_id"),
            ("css", "input[name*='login' i]"),
            ("css", "input[name*='user' i]"),
            ("css", "input[type='text']:first-of-type"),
        ]
        try:
            login_field = wait_for_field_robust(driver, username_selectors)
            log(f"✓ Username field found (using: {login_field.get_attribute('name') or login_field.get_attribute('id')})")
        except Exception as e:
            log(f"✗ Could not find username field: {e}", "ERROR")
            # List all available inputs for debugging
            inputs = driver.find_elements(By.TAG_NAME, "input")
            log(f"  Available input fields: {[i.get_attribute('name') or i.get_attribute('id') or 'unnamed' for i in inputs]}")
            return False, "username_field_not_found", str(e)
        
        login_field.clear()
        login_field.send_keys(username)
        log(f"✓ Username entered: {username}")
        
        # ROBUST: Try multiple selectors for password field
        password_selectors = [
            ("name", "password"),
            ("id", "password"),
            ("css", "input[type='password']"),
            ("css", "input[name*='pass' i]"),
        ]
        try:
            password_field = find_field_robust(driver, password_selectors)
            log(f"✓ Password field found")
        except Exception as e:
            log(f"✗ Could not find password field: {e}", "ERROR")
            return False, "password_field_not_found", str(e)
        
        password_field.clear()
        password_field.send_keys(password)
        log("✓ Password entered")
        
        # ROBUST: Try multiple selectors for submit button
        submit_selectors = [
            ("css", "button[type='submit']"),
            ("css", "input[type='submit']"),
            ("css", "button:contains('Submit')"),
            ("css", "button:contains('Login')"),
            ("xpath", "//button[contains(text(), 'Submit') or contains(text(), 'Login')]"),
            ("css", "button"),  # Last resort - first button
        ]
        try:
            submit_btn = find_field_robust(driver, submit_selectors)
            log(f"✓ Submit button found")
        except Exception as e:
            log(f"✗ Could not find submit button: {e}", "ERROR")
            return False, "submit_button_not_found", str(e)
        
        submit_btn.click()
        log("✓ Login form submitted")
        
        # Wait for TOTP page or error
        time.sleep(2)
        
        # Check for error message
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "invalid" in page_text and ("credentials" in page_text or "username" in page_text or "password" in page_text):
            log("✗ LOGIN FAILED: Invalid username/password detected", "ERROR")
            log("  Page shows: 'Invalid credentials' or similar", "ERROR")
            return False, "invalid_credentials", "Invalid username or password"
        
        if "error" in page_text and "login" in page_text:
            log("✗ LOGIN FAILED: Login error on page", "ERROR")
            return False, "login_error", "Login error message displayed"
        
        # ROBUST: Try multiple selectors for TOTP field
        totp_selectors = [
            ("id", "totp_input"),
            ("name", "totp"),
            ("name", "answers[]"),
            ("css", "input[id*='totp' i]"),
            ("css", "input[name*='totp' i]"),
            ("css", "input[name*='answer' i]"),
            ("css", "input[type='password']:first-of-type"),
            ("xpath", "//input[@id='totp_input' or @name='totp' or @name='answers[]']"),
        ]
        try:
            totp_field = find_field_robust(driver, totp_selectors)
            log(f"✓ TOTP field found (using: {totp_field.get_attribute('name') or totp_field.get_attribute('id')})")
            
            # Generate and enter TOTP
            totp_code = TOTP(totp_secret).now()
            totp_field.clear()
            totp_field.send_keys(totp_code)
            log(f"✓ TOTP entered: {totp_code}")
            
            # ROBUST: Submit TOTP with fallback selectors
            totp_submit_selectors = [
                ("css", "button[type='submit']"),
                ("css", "input[type='submit']"),
                ("xpath", "//button[contains(text(), 'Submit') or contains(text(), 'Verify')]"),
                ("css", "button"),  # Last resort
            ]
            try:
                totp_submit = find_field_robust(driver, totp_submit_selectors)
                totp_submit.click()
                log("✓ TOTP form submitted")
            except Exception as e:
                log(f"✗ Could not find TOTP submit button: {e}", "ERROR")
                return False, "totp_submit_not_found", str(e)
            
            time.sleep(3)
            
            # Check for TOTP error
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            if "invalid" in page_text and ("totp" in page_text or "code" in page_text or "otp" in page_text):
                log("✗ LOGIN FAILED: Invalid TOTP code", "ERROR")
                log("  Possible causes:", "ERROR")
                log("    - TOTP code expired during entry", "ERROR")
                log("    - Wrong TOTP secret configured", "ERROR")
                log("    - Clock sync issue", "ERROR")
                return False, "invalid_totp", "TOTP code rejected by server"
            
            if "success" in page_text or "approved" in page_text:
                log("✓✓✓ LOGIN SUCCESSFUL! ✓✓✓")
                return True, "success", "Token generated successfully"
            
            # Check URL for redirect
            current_url = driver.current_url
            if "sasstocko.broker.tradetron.tech" not in current_url or "success" in current_url:
                log(f"✓✓✓ LOGIN SUCCESSFUL! (Redirect detected)")
                log(f"  Final URL: {current_url.split('?')[0]}")
                return True, "success", f"Redirected to {current_url.split('?')[0]}"
            
            log("⚠ Unclear result - no success message or error detected", "WARN")
            return False, "unclear", "Could not determine login status from page content"
            
        except Exception as e:
            log(f"✗ TOTP field not found: {e}", "ERROR")
            
            # Capture page content for diagnosis
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                current_url = driver.current_url
                log(f"  Current URL: {current_url}", "INFO")
                log(f"  Page content (first 500 chars):", "INFO")
                log(f"  {page_text[:500]}...", "INFO")
                
                # Check for specific error messages
                page_lower = page_text.lower()
                if "invalid" in page_lower:
                    log("  ⚠ Page contains 'Invalid' - credentials likely rejected", "WARN")
                if "error" in page_lower:
                    log("  ⚠ Page contains 'Error' - check page content above", "WARN")
                if "2fa" in page_lower or "two factor" in page_lower or "authenticator" in page_lower:
                    log("  ⚠ Page mentions 2FA/Authenticator - TOTP may be needed but field name changed", "WARN")
                    
                # List all input fields on page
                inputs = driver.find_elements(By.TAG_NAME, "input")
                log(f"  Found {len(inputs)} input fields on page:", "INFO")
                for inp in inputs[:5]:  # Show first 5
                    name = inp.get_attribute("name")
                    type_attr = inp.get_attribute("type")
                    id_attr = inp.get_attribute("id")
                    log(f"    - name='{name}' type='{type_attr}' id='{id_attr}'", "INFO")
                    
            except Exception as page_error:
                log(f"  Could not capture page content: {page_error}", "WARN")
            
            log("  Possible causes:", "ERROR")
            log("    - Login credentials rejected before TOTP page", "ERROR")
            log("    - Page structure changed", "ERROR")
            return False, "totp_field_not_found", "TOTP input field not found on page"
    
    except Exception as e:
        log(f"✗ Login test error: {e}", "ERROR")
        return False, "exception", str(e)
    
    finally:
        if driver:
            driver.quit()
            log("✓ Browser closed")


def run_diagnostics(safe_mode=False):
    """Run all diagnostic phases"""
    print("=" * 70)
    print(f"[GJ114 Diagnostic Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("=" * 70)
    
    results = {
        "env_file": False,
        "env_vars": False,
        "dependencies": False,
        "totp": False,
        "network": False,
        "telegram": False,
        "login": None
    }
    
    # Phase 1: Environment
    env_path = check_env_file()
    if env_path:
        results["env_file"] = True
        results["dependencies"] = check_dependencies()
        results["env_vars"], env_results = validate_env_vars(env_path)
    
    # Phase 2: TOTP
    if results["env_vars"]:
        results["totp"], totp_info = validate_totp()
    
    # Phase 3: Network & Telegram
    results["network"] = check_network()
    results["telegram"] = validate_telegram_config()
    
    # Phase 4: Live Login (unless safe mode)
    if not safe_mode and all([results["env_vars"], results["totp"], results["network"]]):
        login_success, login_status, login_details = test_login_live()
        results["login"] = login_success
        # Send Telegram notification AFTER login completes
        send_telegram_notification(login_success, f"Status: {login_status}. {login_details}")
    elif safe_mode:
        log("\n[Skipping live login test - safe mode]")
    
    # Summary
    print("\n" + "=" * 70)
    print("[SUMMARY]")
    print("=" * 70)
    
    checks = [
        ("Environment File", results["env_file"]),
        ("Environment Variables", results["env_vars"]),
        ("Dependencies", results["dependencies"]),
        ("TOTP Generation", results["totp"]),
        ("Network Connectivity", results["network"]),
        ("Telegram Bot", results["telegram"]),
    ]
    
    for name, status in checks:
        symbol = "✓" if status else "✗"
        print(f"[{symbol}] {name}")
    
    if results["login"] is not None:
        symbol = "✓" if results["login"] else "✗"
        print(f"[{symbol}] Live Login Test")
    else:
        print("[-] Live Login Test (skipped - safe mode)")
    
    # Overall status
    all_config_ok = all([results["env_file"], results["env_vars"], results["dependencies"], 
                         results["totp"], results["network"], results["telegram"]])
    
    print("\n" + "=" * 70)
    if all_config_ok and results["login"] is not False:
        print("[STATUS] ✓ ALL CHECKS PASSED - Ready for production use")
        return 0
    elif results["login"] is False:
        print("[STATUS] ⚠ CONFIG OK but LOGIN FAILED - Check diagnostics above")
        return 1
    else:
        print("[STATUS] ✗ CONFIGURATION ISSUES - Fix errors above before production use")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GJ114 Diagnostic Script")
    parser.add_argument("--safe", action="store_true", help="Run safe mode (no live login)")
    parser.add_argument("--full", action="store_true", help="Run full diagnostic including live login")
    args = parser.parse_args()
    
    safe_mode = args.safe or not args.full
    
    if safe_mode and not args.full:
        print("Running in SAFE MODE (use --full for live login test)")
    
    exit_code = run_diagnostics(safe_mode=safe_mode)
    sys.exit(exit_code)
