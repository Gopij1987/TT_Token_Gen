"""
Bigul Broker API Discovery
Try common Bigul API patterns and endpoints
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('BIGUL-API')

dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)


def discover_bigul_api():
    """
    1. Search for Bigul endpoint hints in page JavaScript
    2. Try common Bigul API patterns
    3. Look for setup/configuration endpoints
    """
    
    username = os.getenv('ALGOSENSE_USERNAME')
    password = os.getenv('ALGOSENSE_PASSWORD')
    
    logger.info("\n" + "="*80)
    logger.info("BIGUL API DISCOVERY - Pattern Analysis")
    logger.info("="*80)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Login
        logger.info("\n[STEP 1] Logging in via Algosense API...")
        session = requests.Session()
        
        phone = str(username).strip()
        if not phone.startswith('+91'):
            phone = phone.lstrip('0')
            phone = f"+91{phone}"
        
        resp = session.post(
            "https://api.algotest.in/login",
            json={"phoneNumber": phone, "password": password},
            timeout=30
        )
        
        if resp.status_code != 200:
            logger.error(f"❌ API login failed: {resp.status_code}")
            return
        
        logger.info("✓ Login successful")
        
        # Transfer to browser
        logger.info("\n[STEP 2] Transferring session to browser...")
        driver.get("https://algotest.in/")
        time.sleep(1)
        
        for name, value in session.cookies.items():
            try:
                driver.add_cookie({'name': name, 'value': value, 'domain': 'algotest.in', 'path': '/'})
            except:
                pass
        
        logger.info("✓ Cookies transferred")
        
        # Go to broker page
        logger.info("\n[STEP 3] Navigating to broker page...")
        driver.get("https://algotest.in/broker")
        time.sleep(3)
        
        # Navigate to "All Brokers" tab first to find Bigul with enabled button
        logger.info("\n[STEP 4] Looking for 'All Brokers' tab...")
        wait = WebDriverWait(driver, 10)
        
        try:
            all_brokers_tab = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'All Brokers')]"))
            )
            logger.info("✓ Found 'All Brokers' tab, clicking...")
            driver.execute_script("arguments[0].click();", all_brokers_tab)
            time.sleep(2)
            logger.info("✓ Clicked 'All Brokers' tab")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not click 'All Brokers': {e}")
        
        # Now look for Bigul in All Brokers
        logger.info("\n[STEP 5] Looking for Bigul card in All Brokers...")
        
        try:
            bigul_elem = wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Bigul')]"))
            )
            logger.info("✓ Found Bigul element")
            
            # Look for card container
            parent = bigul_elem
            for _ in range(10):
                if parent and 'rounded' in str(parent.get_attribute('class') or ''):
                    bigul_card = parent
                    break
                parent = parent.find_element(By.XPATH, "..")
            
            # Find buttons in card
            buttons = bigul_card.find_elements(By.TAG_NAME, "button")
            logger.info(f"  Found {len(buttons)} buttons in Bigul card")
            
            for i, btn in enumerate(buttons):
                btn_text = btn.text.strip()
                if btn_text:
                    is_enabled = btn.get_attribute('disabled') is None
                    logger.info(f"    Button {i}: '{btn_text}' (enabled: {is_enabled})")
                    
                    # If this looks like a Login button and is enabled, try to inspect it
                    if 'login' in btn_text.lower() and is_enabled:
                        logger.info(f"\n  ✓ Found enabled Login button!")
                        logger.info(f"    Button HTML: {btn.get_attribute('outerHTML')[:200]}")
                        
                        # Try to see what happens when we hover (might reveal tooltips/attributes)
                        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                        time.sleep(1)
        
        except Exception as e:
            logger.error(f"❌ Error finding Bigul in All Brokers: {e}")
        
        # Now look for JavaScript hints
        logger.info("\n[STEP 6] Analyzing page JavaScript for API hints...")
        
        # Get all script content
        scripts = driver.find_elements(By.TAG_NAME, "script")
        logger.info(f"  Found {len(scripts)} script tags")
        
        # Look for Bigul-related API calls in page source
        page_source = driver.page_source
        
        # Common patterns to look for
        patterns = [
            'bigul',
            'broker.*login',
            'trading.*api',
            '/api/broker',
            '/broker/login',
            'oauth',
            'authorization'
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(f'["\']([^"\']*{pattern}[^"\']*)["\']', page_source, re.IGNORECASE)
            if matches:
                logger.info(f"  Found '{pattern}' references:")
                for match in set(matches)[:3]:
                    logger.info(f"    - {match}")
        
        # List common Bigul API endpoints to try
        logger.info("\n[STEP 7] Common Bigul API endpoints to test:")
        
        common_endpoints = [
            "https://api.bigul.com/login",
            "https://api.bigul.io/login",
            "https://bigul.api.algotest.in/login",
            "https://algotest.in/api/broker/bigul/login",
            "https://api.algotest.in/broker/bigul/login",
            "https://algotest.in/api/bigul",
        ]
        
        for endpoint in common_endpoints:
            logger.info(f"  - {endpoint}")
        
        # Save page for manual inspection
        html_file = Path(__file__).parent / 'bigul_all_brokers.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"\n✓ All Brokers page saved to: {html_file}")
        
        # Try to take screenshot
        screenshot = Path(__file__).parent / 'bigul_all_brokers.png'
        driver.save_screenshot(str(screenshot))
        logger.info(f"✓ Screenshot saved to: {screenshot}")
        
        logger.info(f"\nNext Steps:")
        logger.info(f"1. Wait for market to open (9:15 AM IST)")
        logger.info(f"2. Run this script again - Login button will be enabled")
        logger.info(f"3. The enabled button's onclick handler will reveal the API endpoint")
        logger.info(f"4. Or: Check the browser DevTools Network tab for the actual API call")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("\n[STEP 8] Closing browser...")
        driver.quit()
        logger.info("✓ Done")


if __name__ == "__main__":
    try:
        discover_bigul_api()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
