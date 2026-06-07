"""
Algosense API Discovery with Selenium + Network Interception
Uses Selenium to capture actual XHR/Fetch requests during login

Requirements:
  pip install selenium requests beautifulsoup4 python-dotenv

Usage:
  python find_algosense_api_selenium.py
"""
import os
import json
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import logging
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment
dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.error("❌ Selenium not installed. Install with: pip install selenium webdriver-manager")
    sys.exit(1)

class AlgosenseSeleniumDiscovery:
    """Discover Algosense API using Selenium for SPA support"""
    
    def __init__(self):
        self.base_url = "https://algotest.in"
        self.login_url = f"{self.base_url}/login"
        self.broker_url = f"{self.base_url}/broker"
        self.tag = "SELENIUM-DISCOVERY"
        self.captured_requests = []
        self.driver = None

    def setup_selenium(self):
        """Setup Selenium WebDriver with network logging"""
        try:
            logger.info(f"[{self.tag}] Setting up Selenium WebDriver...")
            
            chrome_options = Options()
            
            # Disable headless for visibility during testing
            # chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-sync')
            
            # Enable network logging
            chrome_options.add_argument('--enable-automation=False')
            
            # Set user agent
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            logger.info(f"[{self.tag}] Starting Chrome WebDriver...")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Enable performance logging to capture network requests
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            logger.info(f"[{self.tag}] ✓ WebDriver ready")
            return True
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ Selenium setup failed: {e}")
            logger.error(f"[{self.tag}] Make sure Chrome is installed and chromedriver is in PATH")
            logger.error(f"[{self.tag}] Download chromedriver from: https://chromedriver.chromium.org/")
            return False

    def capture_network_requests(self) -> Dict[str, Any]:
        """Capture network requests during login"""
        
        username = os.getenv('ALGOSENSE_USERNAME')
        password = os.getenv('ALGOSENSE_PASSWORD')
        
        if not username or not password:
            logger.error(f"[{self.tag}] ❌ Missing credentials")
            return {}
        
        try:
            logger.info(f"\n[{self.tag}] Opening login page...")
            self.driver.get(self.login_url)
            
            # Wait for page to load
            time.sleep(3)
            
            logger.info(f"[{self.tag}] Page title: {self.driver.title}")
            logger.info(f"[{self.tag}] Current URL: {self.driver.current_url}")
            
            # STEP 1: Find username input
            logger.info(f"\n[{self.tag}] STEP 1: Finding username field...")
            username_field = None
            
            # Try common field selectors
            selectors = [
                (By.NAME, 'username'),
                (By.NAME, 'login'),
                (By.NAME, 'email'),
                (By.NAME, 'user'),
                (By.ID, 'username'),
                (By.ID, 'login'),
                (By.CLASS_NAME, 'username-input'),
                (By.CSS_SELECTOR, 'input[type="text"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="username" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="login" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="email" i]'),
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        username_field = elements[0]
                        logger.info(f"[{self.tag}] Found username field: {selector_type}='{selector_value}'")
                        break
                except:
                    continue
            
            if not username_field:
                logger.error(f"[{self.tag}] ❌ Could not find username field")
                return {}
            
            # STEP 2: Find password input
            logger.info(f"\n[{self.tag}] STEP 2: Finding password field...")
            password_field = None
            
            selectors = [
                (By.NAME, 'password'),
                (By.NAME, 'pass'),
                (By.NAME, 'pwd'),
                (By.ID, 'password'),
                (By.CLASS_NAME, 'password-input'),
                (By.CSS_SELECTOR, 'input[type="password"]'),
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        password_field = elements[0]
                        logger.info(f"[{self.tag}] Found password field: {selector_type}='{selector_value}'")
                        break
                except:
                    continue
            
            if not password_field:
                logger.error(f"[{self.tag}] ❌ Could not find password field")
                return {}
            
            # STEP 3: Enter credentials
            logger.info(f"\n[{self.tag}] STEP 3: Entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            logger.info(f"[{self.tag}] Username entered: {username}")
            
            password_field.clear()
            password_field.send_keys(password)
            logger.info(f"[{self.tag}] Password entered")
            
            # STEP 4: Find and click login button
            logger.info(f"\n[{self.tag}] STEP 4: Finding login button...")
            login_button = None
            
            button_selectors = [
                (By.NAME, 'login'),
                (By.NAME, 'submit'),
                (By.ID, 'login-btn'),
                (By.ID, 'submit-btn'),
                (By.CLASS_NAME, 'login-btn'),
                (By.CLASS_NAME, 'submit-btn'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'button:contains("Login")'),
                (By.XPATH, '//button[contains(text(), "Login")]'),
                (By.XPATH, '//button[contains(text(), "Sign In")]'),
            ]
            
            for selector_type, selector_value in button_selectors:
                try:
                    elements = self.driver.find_elements(selector_type, selector_value)
                    if elements:
                        login_button = elements[0]
                        logger.info(f"[{self.tag}] Found login button")
                        break
                except:
                    continue
            
            if not login_button:
                logger.error(f"[{self.tag}] ❌ Could not find login button")
                return {}
            
            # STEP 5: Enable network monitoring before clicking
            logger.info(f"\n[{self.tag}] STEP 5: Enabling network interception...")
            
            # Get current logs before click
            initial_logs = self.driver.get_log('browser')
            
            # STEP 6: Click login button
            logger.info(f"\n[{self.tag}] STEP 6: Clicking login button...")
            login_button.click()
            
            # Wait for requests to complete
            logger.info(f"[{self.tag}] Waiting for response...")
            time.sleep(5)
            
            # STEP 7: Capture all network activity
            logger.info(f"\n[{self.tag}] STEP 7: Analyzing network requests...")
            
            # Get current page state
            current_url = self.driver.current_url
            logger.info(f"[{self.tag}] Current URL: {current_url}")
            
            # Check browser console for XHR requests info
            logs = self.driver.get_log('browser')
            requests_found = []
            
            for log in logs:
                if 'api' in log['message'].lower() or 'login' in log['message'].lower():
                    requests_found.append(log['message'])
                    logger.info(f"[{self.tag}] Network log: {log['message'][:100]}")
            
            # Try to extract API calls from page source
            page_source = self.driver.page_source
            
            # Look for API endpoints in JavaScript
            import re
            api_pattern = r'(["\'])(https?://[^"\']*api[^"\']*)\1'
            apis_in_page = re.findall(api_pattern, page_source)
            
            if apis_in_page:
                logger.info(f"\n[{self.tag}] Found API endpoints in page source:")
                for api in set(apis_in_page):
                    logger.info(f"[{self.tag}]   • {api[1]}")
            
            # STEP 8: Check if broker page is accessible
            logger.info(f"\n[{self.tag}] STEP 8: Checking broker page...")
            try:
                self.driver.get(self.broker_url)
                time.sleep(2)
                broker_url = self.driver.current_url
                logger.info(f"[{self.tag}] Broker page URL: {broker_url}")
            except:
                logger.warning(f"[{self.tag}] Could not access broker page")
            
            # Compile results
            discovery_results = {
                'timestamp': datetime.now().isoformat(),
                'browser_page_source_length': len(page_source),
                'final_url': current_url,
                'broker_url': self.driver.current_url,
                'network_requests_found': requests_found,
                'apis_in_page': list(set([x[1] for x in apis_in_page])),
                'cookies': [
                    {
                        'name': cookie['name'],
                        'value': cookie['value'][:50] if len(cookie.get('value', '')) > 50 else cookie.get('value', ''),
                        'domain': cookie.get('domain', ''),
                    }
                    for cookie in self.driver.get_cookies()
                ]
            }
            
            return discovery_results
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ Error during capture: {e}", exc_info=True)
            return {}
        finally:
            if self.driver:
                self.driver.quit()

    def generate_report(self, results: Dict[str, Any]):
        """Generate discovery report"""
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║            ALGOSENSE SELENIUM API DISCOVERY REPORT                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

Timestamp: {results.get('timestamp', 'N/A')}

BROWSER STATE AFTER LOGIN:
─────────────────────────────────────────────────────────────────────────────
  Final URL:              {results.get('final_url', 'N/A')}
  Broker URL:             {results.get('broker_url', 'N/A')}
  Page Source Length:     {results.get('browser_page_source_length', 0)} bytes

NETWORK REQUESTS CAPTURED:
─────────────────────────────────────────────────────────────────────────────
"""
        
        if results.get('network_requests_found'):
            for req in results['network_requests_found']:
                report += f"  • {req}\n"
        else:
            report += "  (No new network requests captured)\n"
        
        report += f"\nAPI ENDPOINTS FOUND IN PAGE:\n─────────────────────────────────────────────────────────────────────────────\n"
        
        if results.get('apis_in_page'):
            for api in results['apis_in_page']:
                report += f"  • {api}\n"
        else:
            report += "  (No API endpoints found in page source)\n"
        
        report += f"\nSESSION COOKIES:\n─────────────────────────────────────────────────────────────────────────────\n"
        
        if results.get('cookies'):
            for cookie in results['cookies']:
                report += f"  • {cookie['name']}: {cookie['value']}\n"
        else:
            report += "  (No cookies set)\n"
        
        report += f"""
NEXT STEPS:
═════════════════════════════════════════════════════════════════════════════
1. Check the "APIs found in page" section - these might be the login endpoints

2. If you see API endpoints, try making direct requests:
   curl -X POST https://algotest.in/api/... \\
     -H "Content-Type: application/json" \\
     -d '{{"username":"...","password":"..."}}'

3. Look for these patterns in the output:
   ✓ /api/login
   ✓ /api/auth/login
   ✓ /api/authenticate
   ✓ /api/v1/login
   ✓ /rest/login

4. Share the "API ENDPOINTS FOUND" section with me if any are listed

═════════════════════════════════════════════════════════════════════════════
"""
        
        logger.info(report)
        return report

def main():
    """Main execution"""
    
    logger.info("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ALGOSENSE API DISCOVERY - SELENIUM MODE                                 ║
║                                                                           ║
║  This script will:                                                        ║
║  1. Open https://algotest.in/login in Chrome                             ║
║  2. Fill in credentials from .env.algosense                              ║
║  3. Click login button                                                    ║
║  4. Capture all network activity                                          ║
║  5. Extract API endpoints                                                ║
║                                                                           ║
║  A Chrome window will open - DO NOT CLOSE IT until script finishes       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    discovery = AlgosenseSeleniumDiscovery()
    
    if not discovery.setup_selenium():
        return False
    
    results = discovery.capture_network_requests()
    
    if results:
        report = discovery.generate_report(results)
        
        with open('algosense_selenium_discovery.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info("\n✓ Results saved to algosense_selenium_discovery.json")
        return True
    else:
        logger.error("\n❌ Failed to complete discovery")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
