"""
Discover Broker Login API - Bigul
Click Bigul Login/Re-login button and capture response
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
logger = logging.getLogger('BROKER-LOGIN')

dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)


def discover_broker_login_api():
    """
    Navigate to My Brokers tab and capture Bigul login API call
    """
    
    username = os.getenv('ALGOSENSE_USERNAME')
    password = os.getenv('ALGOSENSE_PASSWORD')
    
    logger.info("\n" + "="*80)
    logger.info("BROKER LOGIN API DISCOVERY - Bigul (My Brokers Tab)")
    logger.info("="*80)
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    logger.info("\n[STEP 1] Starting Chrome browser...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Login via API
        logger.info("[STEP 2] Logging in via Algosense API...")
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
        
        # Transfer cookies to Selenium
        logger.info("[STEP 3] Transferring session cookies to browser...")
        driver.get("https://algotest.in/")
        time.sleep(1)
        
        for name, value in session.cookies.items():
            try:
                driver.add_cookie({'name': name, 'value': value, 'domain': 'algotest.in', 'path': '/'})
                logger.info(f"  ✓ Added cookie: {name}")
            except Exception as e:
                logger.warning(f"  ⚠️  Could not add cookie {name}: {e}")
        
        # Navigate to broker page
        logger.info("[STEP 4] Navigating to /broker page...")
        driver.get("https://algotest.in/broker")
        time.sleep(3)
        logger.info(f"  Current URL: {driver.current_url}")
        logger.info(f"  Page title: {driver.title}")
        
        # Wait for tabs to load
        logger.info("[STEP 5] Waiting for 'My Brokers' tab to appear...")
        wait = WebDriverWait(driver, 15)
        
        try:
            # Look for "My Brokers" tab
            my_brokers_tab = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'My Brokers')]"))
            )
            logger.info("✓ Found 'My Brokers' tab")
            
            # Click it
            logger.info("[STEP 6] Clicking 'My Brokers' tab...")
            driver.execute_script("arguments[0].click();", my_brokers_tab)
            time.sleep(2)
            logger.info("✓ Tab clicked")
            
        except Exception as e:
            logger.error(f"❌ Could not find 'My Brokers' tab: {e}")
            logger.info("\nPage HTML (first 2000 chars):")
            logger.info(driver.page_source[:2000])
            return
        
        # Clear CDP logs before clicking login
        driver.get_log("performance")
        
        # Now find Bigul login button
        logger.info("[STEP 7] Waiting for Bigul card...")
        
        try:
            # Save HTML for inspection
            html_file = Path(__file__).parent / 'broker_page_bigul.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"  Page HTML saved to: {html_file}")
            
            logger.info("[STEP 8] Finding Bigul Login/Re-login button...")
            
            # Find the Bigul Gopi heading/text element
            bigul_heading = driver.find_element(By.XPATH, "//*[text()='Bigul Gopi']")
            logger.info(f"  Found Bigul Gopi broker")
            
            # Get the immediate parent card of Bigul Gopi
            bigul_card_immediate = bigul_heading.find_element(By.XPATH, "ancestor::div[contains(@class, 'border') or contains(@class, 'rounded')][1]")
            
            # Find "Login" or "Re-login" button in Bigul card
            action_button = None
            button_text = None
            
            try:
                # Try "Login" first
                action_button = bigul_card_immediate.find_element(By.XPATH, ".//button[text()='Login']")
                button_text = "Login"
                logger.info(f"  ✓ Found 'Login' button")
            except:
                try:
                    # Try "Re-login"
                    action_button = bigul_card_immediate.find_element(By.XPATH, ".//button[text()='Re-login']")
                    button_text = "Re-login"
                    logger.info(f"  ✓ Found 'Re-login' button")
                except:
                    raise Exception("Neither 'Login' nor 'Re-login' button found in Bigul card")
            
            if action_button:
                logger.info(f"✓ Action button: '{button_text}'")
                logger.info(f"  Button enabled: {not action_button.get_attribute('disabled')}")
                
                # Get broker ID from data attribute
                data_broker = action_button.get_attribute('data-broker')
                if data_broker:
                    logger.info(f"  Broker type: {data_broker}")
            else:
                raise Exception("Could not find action button")
            
            # Check button details
            onclick = action_button.get_attribute('onclick')
            if onclick:
                logger.info(f"  onclick: {onclick}")
            
            # Get common data attributes
            logger.info(f"  data-id: {action_button.get_attribute('data-id')}")
            
            # Take screenshot before clicking
            screenshot_path = Path(__file__).parent / 'broker_before_login.png'
            driver.save_screenshot(str(screenshot_path))
            logger.info(f"  Screenshot saved: {screenshot_path}")
            
            # Click the action button
            logger.info(f"[STEP 9] Clicking Bigul {button_text} button...")
            driver.execute_script("arguments[0].click();", action_button)
            time.sleep(3)
            
            logger.info("✓ Login button clicked")
            logger.info(f"  Current URL: {driver.current_url}")
            
            # STEP 9.5: Check broker status after login attempt
            logger.info("[STEP 9.5] Checking broker status after login...")
            time.sleep(2)  # Wait for page to update
            
            # Refresh page to see updated status
            driver.refresh()
            time.sleep(2)
            
            # Look for status indicators
            try:
                # Check for "LOGGED IN" status
                logged_in_status = driver.find_elements(By.XPATH, "//*[contains(text(), 'LOGGED IN')]")
                logout_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Logout')]")
                relogin_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Re-login')]")
                
                if logged_in_status or (logout_buttons and relogin_buttons):
                    logger.info("✅ BROKER LOGIN SUCCESSFUL!")
                    logger.info(f"  Status: LOGGED IN")
                    logger.info(f"  Logout button found: {len(logout_buttons) > 0}")
                    logger.info(f"  Re-login button found: {len(relogin_buttons) > 0}")
                else:
                    logger.warning("⚠️  Login status unclear - checking page content")
                    
                # Save HTML after login
                html_file = Path(__file__).parent / 'broker_page_after_login.html'
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logger.info(f"  Page HTML saved to: {html_file}")
                
            except Exception as e:
                logger.warning(f"Could not verify status: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error finding/clicking Bigul login: {e}")
            import traceback
            traceback.print_exc()
            
            # Debug: show all visible buttons
            logger.info("\nDebug - All buttons on page:")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for i, btn in enumerate(buttons):
                if btn.is_displayed():
                    logger.info(f"  Button {i}: {btn.text} | class: {btn.get_attribute('class')[:50]}")
            return
        
        # Capture API calls with responses and body data
        logger.info("[STEP 10] Analyzing network requests and responses...")
        logs = driver.get_log("performance")
        
        api_calls = []
        request_by_id = {}
        response_data = {}
        response_body = {}
        
        for entry in logs:
            try:
                msg = json.loads(entry['message'])['message']
                
                # Capture POST/GET requests
                if msg['method'] == 'Network.requestWillBeSent':
                    req = msg['params']['request']
                    url = req['url']
                    method = req['method']
                    request_id = msg['params'].get('requestId', '')
                    
                    # Focus on broker/login related calls
                    if method in ['POST', 'GET'] and any(x in url.lower() for x in ['broker', 'login', 'auth', 'api']):
                        post_data = req.get('postData', '')
                        
                        api_call = {
                            'method': method,
                            'url': url,
                            'postData': post_data,
                            'headers': req.get('headers', {}),
                            'requestId': request_id
                        }
                        api_calls.append(api_call)
                        request_by_id[request_id] = api_call
                
                # Capture responses
                if msg['method'] == 'Network.responseReceived':
                    request_id = msg['params'].get('requestId', '')
                    response = msg['params'].get('response', {})
                    
                    if request_id in request_by_id:
                        response_data[request_id] = {
                            'status': response.get('status', ''),
                            'statusText': response.get('statusText', ''),
                            'headers': response.get('headers', {}),
                            'url': response.get('url', '')
                        }
                
                # Capture response body data
                if msg['method'] == 'Network.getResponseBody':
                    request_id = msg['params'].get('requestId', '')
                    if request_id in request_by_id:
                        body = msg['params'].get('body', '')
                        if body:
                            response_body[request_id] = body
                
            except:
                pass
        
        # Update api_calls with response info
        for api_call in api_calls:
            req_id = api_call.get('requestId')
            if req_id in response_data:
                api_call['response'] = response_data[req_id]
            if req_id in response_body:
                api_call['responseBody'] = response_body[req_id]
        
        # Display results
        if api_calls:
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ CAPTURED {len(api_calls)} API CALLS")
            logger.info(f"{'='*80}\n")
            
            # Find the broker_login call
            broker_api_call = None
            for i, call in enumerate(api_calls, 1):
                logger.info(f"[API Call {i}]")
                logger.info(f"  Method: {call['method']}")
                logger.info(f"  URL: {call['url']}")
                
                if call['postData']:
                    logger.info(f"  Body: {call['postData']}")
                
                # Display response info if available
                if 'response' in call:
                    resp = call['response']
                    logger.info(f"  Response Status: {resp.get('status')} {resp.get('statusText')}")
                    if resp.get('status') == 200:
                        logger.info(f"  ✅ SUCCESS")
                        if 'broker_login' in call['url'].lower() or 'xts_confirm' in call['url'].lower():
                            broker_api_call = call
                
                # Display response body if available
                if 'responseBody' in call:
                    logger.info(f"  Response Body: {call['responseBody'][:200]}")
                
                logger.info("")
            
            # Highlight broker login result
            if broker_api_call:
                logger.info(f"\n{'='*80}")
                logger.info(f"🎯 BIGUL BROKER {button_text.upper()} SUCCESSFUL!")
                logger.info(f"{'='*80}")
                logger.info(f"  Endpoint: {broker_api_call['url']}")
                logger.info(f"  Status: {broker_api_call.get('response', {}).get('status')} {broker_api_call.get('response', {}).get('statusText')}")
                if 'responseBody' in broker_api_call:
                    logger.info(f"  Message: {broker_api_call['responseBody']}")
                logger.info(f"{'='*80}\n")
            
            # Save to file
            output_file = Path(__file__).parent / 'broker_api_calls.json'
            with open(output_file, 'w') as f:
                json.dump(api_calls, f, indent=2)
            logger.info(f"📄 Detailed API calls saved to: {output_file}")
        
        else:
            logger.warning("⚠️  No API calls captured - might be client-side only")
        
        # Take final screenshot
        screenshot_path = Path(__file__).parent / 'broker_after_login.png'
        driver.save_screenshot(str(screenshot_path))
        logger.info(f"\n📸 Final screenshot: {screenshot_path}")
        
        logger.info(f"\nFinal URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("\n[STEP 11] Closing browser...")
        driver.quit()
        logger.info("✓ Done")


if __name__ == "__main__":
    try:
        discover_broker_login_api()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
