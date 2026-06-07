"""
Discover the Broker Login API endpoint

This script:
1. Logs into Algosense (already proven working)
2. Navigates to broker page
3. Uses Chrome DevTools Protocol to capture network requests
4. Identifies the API call when clicking Login for IIFL Markets
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(message)s'
)
logger = logging.getLogger('BROKER-API-DISCOVERY')

# Load environment
dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)


def capture_broker_login_request():
    """Use Selenium + Chrome to capture broker login API call"""
    
    username = os.getenv('ALGOSENSE_USERNAME')
    password = os.getenv('ALGOSENSE_PASSWORD')
    
    logger.info("="*70)
    logger.info("BROKER LOGIN API DISCOVERY - Using Selenium + Network Capture")
    logger.info("="*70)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Enable Chrome logging
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    logger.info("\n[STEP 1] Starting Chrome browser...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # STEP 2: Navigate to login
        logger.info("\n[STEP 2] Navigating to AlgoTest login page...")
        driver.get("https://algotest.in/login")
        time.sleep(3)
        
        # STEP 3: Login via Algosense API (faster)
        logger.info("\n[STEP 3] Logging in via API call (in background)...")
        
        # Format phone
        phone = str(username).strip()
        if not phone.startswith('+91'):
            phone = phone.lstrip('0')
            phone = f"+91{phone}"
        
        # Call login API
        session = requests.Session()
        login_response = session.post(
            "https://api.algotest.in/login",
            json={"phoneNumber": phone, "password": password},
            timeout=30
        )
        
        if login_response.status_code == 200:
            result = login_response.json()
            if result.get('login') is True:
                logger.info("✓ API login successful")
                
                # Get cookies from requests session
                cookies = session.cookies.get_dict()
                logger.info(f"✓ Got {len(cookies)} cookies")
                
                # Add cookies to Selenium
                driver.get("https://algotest.in/home")  # Navigate to establish domain
                for cookie_name, cookie_value in cookies.items():
                    try:
                        driver.add_cookie({
                            'name': cookie_name,
                            'value': cookie_value,
                            'domain': 'algotest.in',
                            'path': '/'
                        })
                    except Exception as e:
                        logger.warning(f"Could not set cookie {cookie_name}: {e}")
                
                logger.info("✓ Cookies transferred to browser")
        else:
            logger.error(f"API login failed: {login_response.status_code}")
            return
        
        # STEP 4: Navigate to broker page
        logger.info("\n[STEP 4] Navigating to broker page...")
        driver.get("https://algotest.in/broker")
        time.sleep(3)
        
        # Clear previous logs
        driver.get_log("performance")
        
        logger.info("[STEP 5] Looking for IIFL Markets Login button...")
        
        # Wait for IIFL Markets card to load
        wait = WebDriverWait(driver, 10)
        
        # Try to find the IIFL Markets card and Login button
        try:
            # Look for all broker cards
            iifl_card = wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "broker-card"))
            )
            
            logger.info(f"✓ Found {len(iifl_card)} broker cards")
            
            # Find IIFL Markets specifically
            iifl_element = None
            for card in iifl_card:
                text = card.text
                if "IIFL" in text:
                    iifl_element = card
                    logger.info(f"✓ Found IIFL Markets card")
                    break
            
            if iifl_element:
                # Find login button within IIFL card
                login_btn = iifl_element.find_element(By.XPATH, ".//button[contains(text(), 'Login')]")
                logger.info(f"✓ Found Login button")
                
                # Log the button details
                button_onclick = login_btn.get_attribute("onclick")
                button_data = login_btn.get_attribute("data-*")
                button_class = login_btn.get_attribute("class")
                
                logger.info(f"\nButton Details:")
                logger.info(f"  onclick: {button_onclick}")
                logger.info(f"  class: {button_class}")
                
                # Clear performance logs before clicking
                driver.get_log("performance")
                
                logger.info("\n[STEP 6] Clicking Login button and capturing network requests...")
                login_btn.click()
                time.sleep(2)
                
                # Capture network logs
                logs = driver.get_log("performance")
                
                api_calls = []
                for log in logs:
                    try:
                        message = json.loads(log['message'])['message']
                        
                        if message['method'] == 'Network.responseReceived':
                            response = message['params']['response']
                            url = response['url']
                            status = response['status']
                            
                            # Filter for API calls
                            if 'api' in url.lower() or 'broker' in url.lower() or '/login' in url.lower():
                                api_calls.append({
                                    'method': 'GET/POST',
                                    'url': url,
                                    'status': status
                                })
                        
                        if message['method'] == 'Network.requestWillBeSent':
                            request = message['params']['request']
                            url = request['url']
                            method = request['method']
                            
                            # Filter for API calls
                            if 'api' in url.lower() or 'broker' in url.lower() or '/login' in url.lower():
                                api_calls.append({
                                    'method': method,
                                    'url': url,
                                    'status': 'pending'
                                })
                    except:
                        pass
                
                if api_calls:
                    logger.info(f"\n✓ Captured {len(api_calls)} API calls:")
                    for i, call in enumerate(api_calls, 1):
                        logger.info(f"\n  [{i}] {call['method']} {call['url']}")
                        logger.info(f"      Status: {call['status']}")
                else:
                    logger.warning("No API calls captured - might be client-side only")
                
                # Check current URL
                current_url = driver.current_url
                logger.info(f"\nCurrent URL after click: {current_url}")
                
                # Save page source for analysis
                page_source = driver.page_source
                if 'iifl' in page_source.lower() or 'login' in page_source.lower():
                    logger.info("✓ Page contains IIFL/login content")
            else:
                logger.warning("Could not find IIFL Markets card")
        
        except TimeoutException:
            logger.error("Timeout waiting for broker cards to load")
        except NoSuchElementException as e:
            logger.error(f"Could not find Login button: {e}")
    
    finally:
        logger.info("\n[CLEANUP] Closing browser...")
        driver.quit()
        logger.info("✓ Browser closed")


def analyze_broker_page_html():
    """Analyze the broker page HTML to find button details"""
    logger.info("\n" + "="*70)
    logger.info("ANALYZING BROKER PAGE HTML")
    logger.info("="*70)
    
    username = os.getenv('ALGOSENSE_USERNAME')
    password = os.getenv('ALGOSENSE_PASSWORD')
    
    session = requests.Session()
    
    # Login via API
    phone = str(username).strip()
    if not phone.startswith('+91'):
        phone = phone.lstrip('0')
        phone = f"+91{phone}"
    
    response = session.post(
        "https://api.algotest.in/login",
        json={"phoneNumber": phone, "password": password},
        timeout=30
    )
    
    if response.status_code == 200:
        logger.info("✓ Login successful")
    else:
        logger.error(f"Login failed: {response.status_code}")
        return
    
    # Fetch broker page
    logger.info("\n[STEP 1] Fetching broker page...")
    broker_response = session.get("https://algotest.in/broker", timeout=30)
    logger.info(f"Status: {broker_response.status_code}")
    
    # Save HTML for analysis
    html_file = Path(__file__).parent / 'broker_page.html'
    with open(html_file, 'w') as f:
        f.write(broker_response.text)
    logger.info(f"✓ HTML saved to: {html_file}")
    
    # Look for IIFL Markets button
    logger.info("\n[STEP 2] Searching for IIFL Markets Login button...")
    
    import re
    
    # Find all buttons
    buttons = re.findall(r'<button[^>]*>.*?</button>', broker_response.text, re.DOTALL)
    logger.info(f"Found {len(buttons)} buttons in page")
    
    # Look for IIFL or Login
    for i, button in enumerate(buttons):
        if 'IIFL' in broker_response.text[max(0, broker_response.text.find(button)-500):broker_response.text.find(button)+500]:
            logger.info(f"\n[Button {i}] Found button near IIFL:")
            logger.info(f"  {button[:200]}...")
        elif 'Login' in button and 'disabled' not in button:
            logger.info(f"\n[Button {i}] Found Login button:")
            logger.info(f"  {button[:200]}...")
    
    # Look for API endpoints in HTML
    logger.info("\n[STEP 3] Searching for API endpoints in HTML...")
    
    api_patterns = re.findall(r'["\'](/[a-zA-Z0-9/_-]*api[a-zA-Z0-9/_-]*)["\']', broker_response.text)
    
    if api_patterns:
        logger.info(f"Found {len(set(api_patterns))} unique API endpoints:")
        for endpoint in set(api_patterns):
            if 'broker' in endpoint.lower() or 'login' in endpoint.lower():
                logger.info(f"  📍 {endpoint}")
    
    # Look for data attributes that might indicate broker ID
    logger.info("\n[STEP 4] Searching for broker identifiers...")
    
    iifl_pattern = re.findall(r'(?:broker["\']?\s*[:=]\s*["\']?([^"\'>\s]+)["\']?)', broker_response.text, re.IGNORECASE)
    
    if iifl_pattern:
        logger.info(f"Found potential broker IDs: {set(iifl_pattern)}")


if __name__ == "__main__":
    try:
        # Try HTML analysis first (faster, no browser)
        analyze_broker_page_html()
        
        # Then try browser-based capture
        logger.info("\n" + "="*70)
        logger.info("\nNow attempting browser-based network capture...")
        capture_broker_login_request()
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
