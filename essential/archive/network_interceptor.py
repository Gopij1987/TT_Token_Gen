"""
Network Interceptor - Captures all API calls during OAuth login
Helps us understand the exact API endpoints and data format
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from pyotp import TOTP
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import logging

# Setup logging to file
logging.basicConfig(
    filename='network_capture.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv_path = Path(__file__).parent / '.env.GJ114'
load_dotenv(dotenv_path)

# Store captured requests
captured_requests = []
captured_responses = []

def log_request(request):
    """Callback for capturing requests"""
    global captured_requests
    try:
        req_data = {
            'timestamp': time.time(),
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'body': request.body if hasattr(request, 'body') else None
        }
        captured_requests.append(req_data)
        print(f"\n{'='*70}")
        print(f"[REQUEST] {request.method} {request.url}")
        print(f"{'='*70}")
        print(f"Headers: {dict(request.headers)}")
        if request.body:
            print(f"Body: {request.body}")
        logger.info(f"REQUEST: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Body: {request.body}")
    except Exception as e:
        print(f"Error logging request: {e}")

def log_response(response):
    """Callback for capturing responses"""
    global captured_responses
    try:
        resp_data = {
            'timestamp': time.time(),
            'url': response.url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response.text[:500] if response.text else None,  # First 500 chars
            'cookies': dict(response.cookies)
        }
        captured_responses.append(resp_data)
        print(f"\n{'='*70}")
        print(f"[RESPONSE] {response.status_code} {response.url}")
        print(f"{'='*70}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Cookies: {dict(response.cookies)}")
        print(f"Body (first 500 chars): {response.text[:500]}")
        logger.info(f"RESPONSE: {response.status_code} {response.url}")
        logger.debug(f"Headers: {dict(response.headers)}")
        logger.debug(f"Body: {response.text[:500]}")
    except Exception as e:
        print(f"Error logging response: {e}")

class NetworkInterceptor:
    """Intercepts network calls using Chrome DevTools Protocol"""
    
    def __init__(self):
        self.base_url = "https://sasstocko.broker.tradetron.tech"
        self.tag = "CAPTURE"
        self.session = requests.Session()
        self.captured_data = {
            'requests': [],
            'responses': [],
            'endpoints': {}
        }

    def capture_with_requests_logging(self, auth_code):
        """
        Capture API calls by hooking into requests library
        """
        username = os.getenv('STOCKO_USERNAME')
        password = os.getenv('STOCKO_PASSWORD')
        totp_secret = os.getenv('STOCKO_TOTP_SECRET')

        # Hook requests library to log all calls
        print("\n" + "="*70)
        print("[NETWORK INTERCEPTOR] Starting capture...")
        print("="*70)
        
        # Register hooks
        hooks = {
            'response': self.response_hook
        }

        try:
            # Step 1: Load login page
            print(f"\n[STEP 1] Loading login page...")
            login_url = f"{self.base_url}/auth/{auth_code}"
            print(f"URL: {login_url}")
            
            # This will redirect to actual OAuth endpoint
            response = self.session.get(login_url, hooks=hooks, allow_redirects=True)
            print(f"Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            print(f"Cookies: {dict(self.session.cookies)}")

            # Step 2: Get login form
            print(f"\n[STEP 2] Getting login form...")
            form_response = self.session.get(response.url)
            print(f"Status: {form_response.status_code}")
            
            # Extract CSRF token and challenge
            import re
            csrf_match = re.search(r'name="_csrf_token"\s+value="([^"]+)"', form_response.text)
            challenge_match = re.search(r'name="login_challenge"\s+value="([^"]+)"', form_response.text)
            
            csrf_token = csrf_match.group(1) if csrf_match else None
            login_challenge = challenge_match.group(1) if challenge_match else None
            
            print(f"CSRF Token: {csrf_token}")
            print(f"Login Challenge: {login_challenge}")
            
            # Step 3: Submit login credentials
            print(f"\n[STEP 3] Submitting login credentials...")
            login_data = {
                'login_id': username,
                'password': password,
                'login_challenge': login_challenge,
                '_csrf_token': csrf_token
            }
            print(f"Login Data: {login_data}")
            
            login_response = self.session.post(
                response.url,
                data=login_data,
                hooks=hooks,
                allow_redirects=True
            )
            print(f"Status: {login_response.status_code}")
            print(f"Final URL: {login_response.url}")

            # Step 4: Get TOTP form
            print(f"\n[STEP 4] Getting TOTP form...")
            totp_page = self.session.get(login_response.url)
            print(f"Status: {totp_page.status_code}")
            print(f"URL: {totp_page.url}")
            
            # Extract TOTP form data
            totp_match = re.search(r'name="answers\[\]"', totp_page.text)
            twofa_token_match = re.search(r'name="twofa_token"\s+value="([^"]+)"', totp_page.text)
            
            twofa_token = twofa_token_match.group(1) if twofa_token_match else None
            print(f"TOTP Field Found: {bool(totp_match)}")
            print(f"2FA Token: {twofa_token}")

            # Step 5: Generate and submit TOTP
            print(f"\n[STEP 5] Generating and submitting TOTP...")
            totp_code = TOTP(totp_secret).now()
            print(f"TOTP Code: {totp_code}")
            
            totp_data = {
                'answers[]': totp_code,
                'twofa_token': twofa_token if twofa_token else ''
            }
            print(f"TOTP Data: {totp_data}")
            
            totp_response = self.session.post(
                login_response.url,
                data=totp_data,
                hooks=hooks,
                allow_redirects=True
            )
            print(f"Status: {totp_response.status_code}")
            print(f"Final URL: {totp_response.url}")

            # Step 6: Check success
            print(f"\n[STEP 6] Checking for success page...")
            final_page = self.session.get(totp_response.url if totp_response.status_code == 200 else totp_response.url)
            print(f"Status: {final_page.status_code}")
            print(f"Final URL: {final_page.url}")
            
            if 'success' in final_page.url.lower() or 'success' in final_page.text.lower():
                print("[✓] SUCCESS PAGE DETECTED!")
            else:
                print("[✗] Success page not detected")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def response_hook(self, r, *args, **kwargs):
        """Hook to log responses"""
        try:
            print(f"\n{'='*70}")
            print(f"[RESPONSE] {r.status_code} {r.url}")
            print(f"{'='*70}")
            print(f"Headers: {dict(r.headers)}")
            print(f"Cookies: {dict(r.cookies)}")
            # Print only first 500 chars of body
            if r.text:
                print(f"Body (first 500 chars):\n{r.text[:500]}")
                
                # Try to parse JSON if it's JSON response
                try:
                    json_data = r.json()
                    print(f"JSON: {json.dumps(json_data, indent=2)[:500]}")
                except:
                    pass
        except Exception as e:
            print(f"Error in response hook: {e}")
        return r


def main():
    print("="*70)
    print("NETWORK INTERCEPTOR - OAuth Login Call Capture")
    print("="*70)
    print("\nThis script will capture all API calls made during login.")
    print("Results will be saved to: network_capture.log\n")

    auth_code = os.getenv('STOCKO_AUTH_CODE')
    if not auth_code:
        print("ERROR: STOCKO_AUTH_CODE not set in .env.GJ114")
        sys.exit(1)

    interceptor = NetworkInterceptor()
    interceptor.capture_with_requests_logging(auth_code)
    
    print("\n" + "="*70)
    print("[COMPLETE] Network capture finished!")
    print("="*70)
    print("\nCaptured data saved to: network_capture.log")
    print("\nNext steps:")
    print("1. Review the log file for API endpoints and data format")
    print("2. Create API-based login script using this information")


if __name__ == "__main__":
    main()
