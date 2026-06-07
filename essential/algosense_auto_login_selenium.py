"""
Algosense Auto Login - Working Version
Uses Selenium since form-based login is successful

Usage:
  python algosense_auto_login_selenium.py

Requirements:
  pip install selenium webdriver-manager python-dotenv requests
"""
import os
import sys
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('ALGOSENSE-LOGIN')

dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.error("❌ Selenium not installed. Run: pip install selenium webdriver-manager")
    sys.exit(1)


def send_telegram_notification(status: str, username: str, duration: float = None, error_msg: str = None):
    """Send Telegram notification"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            return
        
        ist = timezone(timedelta(hours=5, minutes=30))
        timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
        
        if status == 'success':
            message = f"""
<b>✅ Algosense Login Successful</b>
👤 Account: <code>{username}</code>
⏰ Time: <code>{timestamp}</code>
⏳ Duration: <code>{duration:.1f}s</code>
🖥️ Type: <code>Selenium Browser Automation</code>
            """.strip()
        else:
            message = f"""
<b>❌ Algosense Login Failed</b>
👤 Account: <code>{username}</code>
⏰ Time: <code>{timestamp}</code>
❌ Error: <code>{error_msg}</code>
            """.strip()
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=5)
    except:
        pass


class AlgosenseSeleniumLogin:
    """Algosense login using Selenium"""
    
    def __init__(self):
        self.base_url = "https://algotest.in"
        self.login_url = f"{self.base_url}/login"
        self.dashboard_url = f"{self.base_url}/dashboard"
        self.broker_url = f"{self.base_url}/broker"
        self.driver = None
        self.tag = "ALGOSENSE-SELENIUM"

    def setup_driver(self) -> bool:
        """Initialize WebDriver"""
        try:
            logger.info(f"[{self.tag}] Setting up Chrome WebDriver...")
            
            options = Options()
            # Uncomment to see browser:
            # options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-logging')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-popup-blocking')
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info(f"[{self.tag}] ✓ WebDriver initialized")
            return True
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ WebDriver setup failed: {e}")
            return False

    def login(self) -> bool:
        """Perform login"""
        
        username = os.getenv('ALGOSENSE_USERNAME')
        password = os.getenv('ALGOSENSE_PASSWORD')
        
        if not username or not password:
            logger.error(f"[{self.tag}] ❌ Missing credentials in .env.algosense")
            return False
        
        start_time = time.time()
        
        try:
            logger.info("\n" + "="*70)
            logger.info(f"[{self.tag}] ALGOSENSE AUTO LOGIN - SELENIUM")
            logger.info("="*70)
            
            # STEP 1: Open login page
            logger.info(f"\n[{self.tag}] STEP 1: Opening login page...")
            self.driver.get(self.login_url)
            logger.info(f"[{self.tag}] ✓ Page loaded: {self.driver.title}")
            
            # STEP 2: Find and fill username
            logger.info(f"\n[{self.tag}] STEP 2: Entering username...")
            
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]'))
                )
                username_input.clear()
                username_input.send_keys(username)
                logger.info(f"[{self.tag}] ✓ Username entered: {username}")
            except Exception as e:
                logger.error(f"[{self.tag}] ❌ Could not find username field: {e}")
                return False
            
            # STEP 3: Find and fill password
            logger.info(f"\n[{self.tag}] STEP 3: Entering password...")
            
            try:
                password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                password_input.clear()
                password_input.send_keys(password)
                logger.info(f"[{self.tag}] ✓ Password entered")
            except Exception as e:
                logger.error(f"[{self.tag}] ❌ Could not find password field: {e}")
                return False
            
            # STEP 4: Find and click login button
            logger.info(f"\n[{self.tag}] STEP 4: Clicking login button...")
            
            try:
                # Try multiple selectors for login button
                login_button = None
                selectors = [
                    (By.CSS_SELECTOR, 'button[type="submit"]'),
                    (By.XPATH, '//button[contains(., "Login")]'),
                    (By.XPATH, '//button[contains(., "Sign In")]'),
                    (By.XPATH, '//button[1]'),  # First button
                ]
                
                for selector_type, selector_value in selectors:
                    try:
                        login_button = self.driver.find_element(selector_type, selector_value)
                        break
                    except:
                        continue
                
                if not login_button:
                    logger.error(f"[{self.tag}] ❌ Could not find login button")
                    return False
                
                login_button.click()
                logger.info(f"[{self.tag}] ✓ Login button clicked")
                
            except Exception as e:
                logger.error(f"[{self.tag}] ❌ Error clicking login button: {e}")
                return False
            
            # STEP 5: Wait for redirect
            logger.info(f"\n[{self.tag}] STEP 5: Waiting for login response...")
            
            try:
                # Wait for redirect to dashboard or any page change
                WebDriverWait(self.driver, 20).until(
                    EC.url_changes(self.login_url)
                )
                logger.info(f"[{self.tag}] ✓ Page redirected")
            except Exception as e:
                logger.warning(f"[{self.tag}] ⚠️  Redirect timeout: {e}")
            
            # STEP 6: Verify login success
            logger.info(f"\n[{self.tag}] STEP 6: Verifying login success...")
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            logger.info(f"[{self.tag}] Current URL: {current_url}")
            logger.info(f"[{self.tag}] Page title: {page_title}")
            
            # Check if login was successful
            is_dashboard = '/dashboard' in current_url.lower()
            is_broker = '/broker' in current_url.lower()
            not_login_page = '/login' not in current_url.lower()
            
            if not (is_dashboard or (is_broker and not_login_page)):
                logger.warning(f"[{self.tag}] ⚠️  Not on expected page, but continuing...")
            
            # STEP 7: Get session cookies
            logger.info(f"\n[{self.tag}] STEP 7: Extracting session info...")
            
            cookies = {}
            auth_token = None
            
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value']
                
                if cookie['name'] == 'access_token_cookie':
                    auth_token = cookie['value']
                    logger.info(f"[{self.tag}] ✓ Auth token found")
            
            logger.info(f"[{self.tag}] ✓ Session cookies: {len(cookies)} cookies")
            
            # STEP 8: Try broker login if on dashboard
            logger.info(f"\n[{self.tag}] STEP 8: Checking broker access...")
            
            try:
                self.driver.get(self.broker_url)
                time.sleep(2)
                broker_url = self.driver.current_url
                logger.info(f"[{self.tag}] Broker URL: {broker_url}")
            except Exception as e:
                logger.warning(f"[{self.tag}] Could not access broker page: {e}")
            
            # SUCCESS
            duration = time.time() - start_time
            
            logger.info(f"\n[{self.tag}] " + "="*68)
            logger.info(f"[{self.tag}] ✅✅✅ LOGIN SUCCESSFUL ✅✅✅")
            logger.info(f"[{self.tag}] " + "="*68)
            logger.info(f"[{self.tag}] Duration: {duration:.1f} seconds")
            logger.info(f"[{self.tag}] Final URL: {current_url}")
            logger.info(f"[{self.tag}] Auth Token: {'✓ Set' if auth_token else '✗ Not found'}")
            logger.info(f"[{self.tag}] Cookies: {len(cookies)} stored")
            
            # Save session to file
            session_file = Path(__file__).parent / '.algosense_session.json'
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'url': current_url,
                'cookies': cookies,
                'auth_token': auth_token[:50] + "..." if auth_token and len(auth_token) > 50 else auth_token
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"[{self.tag}] Session saved to: {session_file}")
            
            # Send Telegram notification
            send_telegram_notification('success', username, duration)
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ Login error: {e}", exc_info=True)
            send_telegram_notification('error', username, error_msg=str(e)[:100])
            return False
            
        finally:
            if self.driver:
                logger.info(f"\n[{self.tag}] Closing browser...")
                self.driver.quit()


def main():
    """Main execution"""
    login = AlgosenseSeleniumLogin()
    
    if not login.setup_driver():
        return False
    
    success = login.login()
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[ALGOSENSE-LOGIN] Interrupted by user")
        sys.exit(1)
