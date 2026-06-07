"""
Discover Broker Login API using Chrome DevTools Protocol
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

logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
logger = logging.getLogger('BROKER-CDP')

dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)


def discover_broker_api():
    """Use CDP to capture broker login network request"""
    
    username = os.getenv('ALGOSENSE_USERNAME')
    password = os.getenv('ALGOSENSE_PASSWORD')
    
    logger.info("="*70)
    logger.info("BROKER LOGIN API DISCOVERY - CDP Method")
    logger.info("="*70)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    logger.info("\n[1] Starting Chrome with CDP...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    captured_requests = []
    
    try:
        # Login via API first
        logger.info("[2] Logging in via Algosense API...")
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
            logger.error(f"API login failed: {resp.status_code}")
            return
        
        logger.info("✓ API login successful")
        
        # Transfer cookies to browser
        logger.info("[3] Transferring session to browser...")
        driver.get("https://algotest.in/")
        time.sleep(1)
        
        for name, value in session.cookies.items():
            try:
                driver.add_cookie({'name': name, 'value': value, 'domain': 'algotest.in', 'path': '/'})
            except:
                pass
        
        logger.info("✓ Cookies set")
        
        # Clear CDP logs
        driver.get_log("performance")
        
        # Navigate to broker page
        logger.info("[4] Navigating to broker page...")
        driver.get("https://algotest.in/broker")
        time.sleep(4)
        
        # Give time for JavaScript to render
        logger.info("[5] Waiting for broker cards to render...")
        wait = WebDriverWait(driver, 15)
        
        try:
            # Wait for buttons to appear in DOM
            buttons = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "button")))
            logger.info(f"✓ Found {len(buttons)} buttons on page")
            
            # Find Login buttons
            login_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'login')]")
            logger.info(f"✓ Found {len(login_buttons)} Login buttons")
            
            if login_buttons:
                for i, btn in enumerate(login_buttons):
                    try:
                        btn_text = btn.text
                        btn_class = btn.get_attribute('class')
                        parent_text = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card') or contains(@class, 'broker')]").text if i == 1 else "..."
                        
                        logger.info(f"\n  Button {i+1}:")
                        logger.info(f"    Text: {btn_text}")
                        logger.info(f"    Class: {btn_class[:100] if btn_class else 'N/A'}")
                        logger.info(f"    Parent context: {parent_text[:100]}...")
                    except:
                        pass
        
        except Exception as e:
            logger.warning(f"Could not find buttons: {e}")
        
        # Clear logs before clicking
        driver.get_log("performance")
        
        logger.info("\n[6] Clicking IIFL Markets Login button...")
        
        try:
            # Find IIFL card and click its login button
            iifl_login = driver.find_element(By.XPATH, 
                "//div[contains(text(), 'IIFL')]/..//button[contains(text(), 'Login')]")
            
            button_info = {
                'onclick': iifl_login.get_attribute('onclick'),
                'data_attrs': {k: iifl_login.get_attribute(k) for k in iifl_login.get_attributes() if k.startswith('data-')},
                'class': iifl_login.get_attribute('class')
            }
            logger.info(f"✓ Found IIFL Login button")
            logger.info(f"\nButton Details:")
            logger.info(f"  onclick: {button_info['onclick']}")
            logger.info(f"  data attrs: {button_info['data_attrs']}")
            
            iifl_login.click()
            time.sleep(3)
            
        except Exception as e:
            logger.warning(f"Could not find IIFL Login button: {e}")
            logger.info("Trying alternative selector...")
            
            try:
                # Try finding by parent context
                all_buttons = driver.find_elements(By.XPATH, "//button")
                for btn in all_buttons:
                    if 'Login' in btn.text:
                        parent = btn.find_element(By.XPATH, "ancestor::div[1]")
                        if 'IIFL' in parent.text or 'IIFL' in driver.page_source[
                            max(0, driver.execute_script("return arguments[0].offsetParent.innerHTML", btn).find('IIFL')-200):
                            driver.execute_script("return arguments[0].offsetParent.innerHTML", btn).find('IIFL')+200
                        ]:
                            logger.info("Found IIFL Login button via alternative method")
                            btn.click()
                            time.sleep(3)
                            break
            except:
                pass
        
        # Capture network logs
        logger.info("[7] Analyzing network requests...")
        logs = driver.get_log("performance")
        
        api_calls = {}
        
        for entry in logs:
            try:
                msg = json.loads(entry['message'])['message']
                
                # Capture requests
                if msg['method'] == 'Network.requestWillBeSent':
                    req = msg['params']['request']
                    url = req['url']
                    method = req['method']
                    headers = req.get('headers', {})
                    
                    if any(x in url for x in ['api', 'broker', 'login', '/socket', 'algotest']):
                        api_calls[url] = {
                            'method': method,
                            'headers': headers,
                            'post_data': req.get('postData', '')
                        }
                
                # Capture responses
                if msg['method'] == 'Network.responseReceived':
                    resp = msg['params']['response']
                    url = resp['url']
                    status = resp['status']
                    
                    if url in api_calls:
                        api_calls[url]['status'] = status
                        api_calls[url]['mime_type'] = resp.get('mimeType', '')
                        
            except:
                pass
        
        if api_calls:
            logger.info(f"\n✓ Captured {len(api_calls)} API calls:\n")
            
            for url, details in sorted(api_calls.items()):
                logger.info(f"[{details['method']}] {url}")
                if details.get('status'):
                    logger.info(f"  Status: {details['status']}")
                if details.get('post_data'):
                    logger.info(f"  Body: {details['post_data'][:200]}")
                logger.info("")
        else:
            logger.warning("No API calls captured")
        
        # Check current URL
        current_url = driver.current_url
        logger.info(f"Current URL: {current_url}")
        
        # Check page title
        logger.info(f"Page title: {driver.title}")
        
        # Return captured data
        return api_calls
        
    finally:
        logger.info("\n[8] Closing browser...")
        driver.quit()
        logger.info("✓ Done")


if __name__ == "__main__":
    try:
        discover_broker_api()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
