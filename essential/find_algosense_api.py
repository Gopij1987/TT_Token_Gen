"""
Algosense API Endpoint Discovery Script
Automates login and captures network requests to identify API endpoints

Requirements:
  pip install selenium requests beautifulsoup4 python-dotenv

Usage:
  python find_algosense_api.py
"""
import os
import json
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('algosense_api_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment
dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)

class AlgosenseAPIDiscovery:
    """Discover Algosense API endpoints through automated login"""
    
    def __init__(self):
        self.base_url = "https://algotest.in"
        self.login_url = f"{self.base_url}/login"
        self.broker_url = f"{self.base_url}/broker"
        self.session = requests.Session()
        self.captured_requests = []
        self.tag = "API-DISCOVERY"
        
        # Headers that mimic real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
        })

    def capture_login_requests(self) -> Dict[str, Any]:
        """Capture all network requests during login"""
        
        logger.info("="*70)
        logger.info(f"[{self.tag}] Starting API Endpoint Discovery")
        logger.info("="*70)
        
        username = os.getenv('ALGOSENSE_USERNAME')
        password = os.getenv('ALGOSENSE_PASSWORD')
        
        if not username or not password:
            logger.error(f"[{self.tag}] ❌ Missing credentials in .env.algosense")
            logger.error(f"[{self.tag}] Required: ALGOSENSE_USERNAME, ALGOSENSE_PASSWORD")
            return {}
        
        logger.info(f"[{self.tag}] Username: {username}")
        logger.info(f"[{self.tag}] Target: {self.login_url}")
        
        try:
            # STEP 1: Get login page
            logger.info(f"\n[{self.tag}] STEP 1: Fetching login page...")
            response = self.session.get(self.login_url, timeout=30)
            self._log_request_details(response, self.login_url, "GET", None)
            
            if response.status_code >= 400:
                logger.error(f"[{self.tag}] ❌ Failed to fetch login page: {response.status_code}")
                return {}
            
            # STEP 2: Extract form details
            logger.info(f"\n[{self.tag}] STEP 2: Analyzing login form...")
            form_info = self._extract_form_info(response.text)
            logger.info(f"[{self.tag}] Form action: {form_info.get('action', 'N/A')}")
            logger.info(f"[{self.tag}] Form method: {form_info.get('method', 'POST').upper()}")
            logger.info(f"[{self.tag}] Form fields: {list(form_info.get('fields', {}).keys())}")
            
            # STEP 3: Prepare login data
            logger.info(f"\n[{self.tag}] STEP 3: Preparing login payload...")
            login_data = form_info.get('fields', {}).copy()
            
            # Detect and fill username/password fields
            for field_name in login_data.keys():
                field_lower = field_name.lower()
                if any(x in field_lower for x in ['username', 'login', 'email', 'user', 'userid']):
                    login_data[field_name] = username
                    logger.info(f"[{self.tag}] Auto-detected username field: {field_name}")
                elif any(x in field_lower for x in ['password', 'pass', 'pwd']):
                    login_data[field_name] = password
                    logger.info(f"[{self.tag}] Auto-detected password field: {field_name}")
            
            logger.info(f"[{self.tag}] Payload fields: {list(login_data.keys())}")
            
            # STEP 4: Submit login
            logger.info(f"\n[{self.tag}] STEP 4: Submitting login credentials...")
            
            # Determine submit URL
            submit_url = response.url
            if form_info.get('action'):
                if form_info['action'].startswith('http'):
                    submit_url = form_info['action']
                elif form_info['action'].startswith('/'):
                    submit_url = self.base_url + form_info['action']
                else:
                    submit_url = self.base_url + '/' + form_info['action']
            
            logger.info(f"[{self.tag}] Submit URL: {submit_url}")
            
            auth_response = self.session.post(
                submit_url,
                data=login_data,
                allow_redirects=True,
                timeout=30
            )
            
            self._log_request_details(
                auth_response, 
                submit_url, 
                "POST", 
                login_data
            )
            
            logger.info(f"[{self.tag}] Response status: {auth_response.status_code}")
            logger.info(f"[{self.tag}] Final URL: {auth_response.url}")
            
            # STEP 5: Check for broker page
            logger.info(f"\n[{self.tag}] STEP 5: Checking for broker page...")
            broker_response = self.session.get(self.broker_url, timeout=30)
            self._log_request_details(broker_response, self.broker_url, "GET", None)
            
            # STEP 6: Analyze broker page
            logger.info(f"\n[{self.tag}] STEP 6: Analyzing broker page for login form...")
            broker_form_info = self._extract_form_info(broker_response.text)
            if broker_form_info.get('action'):
                logger.info(f"[{self.tag}] Broker form action: {broker_form_info['action']}")
                logger.info(f"[{self.tag}] Broker form fields: {list(broker_form_info.get('fields', {}).keys())}")
            
            # Compile discoveries
            discovery_results = {
                'timestamp': datetime.now().isoformat(),
                'login_endpoint': {
                    'url': submit_url,
                    'method': form_info.get('method', 'POST').upper(),
                    'fields': list(login_data.keys()),
                    'response_status': auth_response.status_code,
                    'response_url': auth_response.url,
                },
                'broker_endpoint': {
                    'url': self.broker_url,
                    'method': 'GET',
                    'response_status': broker_response.status_code,
                } if broker_form_info.get('action') else None,
                'session_cookies': dict(self.session.cookies),
            }
            
            return discovery_results
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ Discovery error: {e}", exc_info=True)
            return {}

    def _extract_form_info(self, html: str) -> Dict[str, Any]:
        """Extract form information from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            form = soup.find('form')
            
            if not form:
                return {'fields': {}, 'action': '', 'method': 'POST'}
            
            form_info = {
                'action': form.get('action', ''),
                'method': form.get('method', 'POST'),
                'fields': {}
            }
            
            for input_field in form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_info['fields'][name] = value
            
            return form_info
        except Exception as e:
            logger.error(f"[{self.tag}] Error extracting form: {e}")
            return {'fields': {}, 'action': '', 'method': 'POST'}

    def _log_request_details(self, response: requests.Response, url: str, method: str, payload: Dict = None):
        """Log detailed request/response information"""
        
        logger.info(f"\n  ┌─ REQUEST ─────────────────────────────────────────┐")
        logger.info(f"  │ URL:    {url}")
        logger.info(f"  │ Method: {method}")
        if payload:
            logger.info(f"  │ Payload fields: {list(payload.keys())}")
        logger.info(f"  └─────────────────────────────────────────────────────┘")
        
        logger.info(f"  ┌─ RESPONSE ────────────────────────────────────────┐")
        logger.info(f"  │ Status: {response.status_code}")
        logger.info(f"  │ URL: {response.url}")
        logger.info(f"  │ Content-Type: {response.headers.get('content-type', 'N/A')}")
        logger.info(f"  │ Content-Length: {len(response.text)} bytes")
        
        # Log response headers of interest
        interesting_headers = [
            'set-cookie', 'authorization', 'x-auth-token', 
            'x-session-id', 'access-token', 'token'
        ]
        for header in interesting_headers:
            value = response.headers.get(header)
            if value:
                # Truncate token/cookie values
                display_value = value[:50] + "..." if len(value) > 50 else value
                logger.info(f"  │ {header}: {display_value}")
        
        logger.info(f"  └─────────────────────────────────────────────────────┘")
        
        # Try to parse and log response body
        try:
            if 'json' in response.headers.get('content-type', ''):
                data = response.json()
                logger.info(f"  ┌─ RESPONSE JSON ───────────────────────────────────┐")
                # Log keys only (not values for security)
                logger.info(f"  │ Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key in ['token', 'access_token', 'sessionId', 'session_id', 'success']:
                            display_val = str(value)[:40] + "..." if len(str(value)) > 40 else value
                            logger.info(f"  │ {key}: {display_val}")
                logger.info(f"  └─────────────────────────────────────────────────────┘")
        except:
            pass

    def generate_report(self, results: Dict[str, Any]):
        """Generate a formatted report of findings"""
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                 ALGOSENSE API ENDPOINT DISCOVERY REPORT                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

Timestamp: {results.get('timestamp', 'N/A')}

┌─ LOGIN ENDPOINT ──────────────────────────────────────────────────────────┐
│
│  URL:              {results.get('login_endpoint', {}).get('url', 'N/A')}
│  Method:           {results.get('login_endpoint', {}).get('method', 'N/A')}
│  Request Fields:   {', '.join(results.get('login_endpoint', {}).get('fields', []))}
│  Response Status:  {results.get('login_endpoint', {}).get('response_status', 'N/A')}
│  Response URL:     {results.get('login_endpoint', {}).get('response_url', 'N/A')}
│
└───────────────────────────────────────────────────────────────────────────┘

┌─ BROKER ENDPOINT ─────────────────────────────────────────────────────────┐
│
│  URL:              {results.get('broker_endpoint', {}).get('url', 'N/A') if results.get('broker_endpoint') else 'Not found'}
│  Method:           {results.get('broker_endpoint', {}).get('method', 'N/A') if results.get('broker_endpoint') else 'N/A'}
│  Response Status:  {results.get('broker_endpoint', {}).get('response_status', 'N/A') if results.get('broker_endpoint') else 'N/A'}
│
└───────────────────────────────────────────────────────────────────────────┘

┌─ SESSION INFORMATION ──────────────────────────────────────────────────────┐
│
│  Cookies Set: {len(results.get('session_cookies', {}))} cookies
"""
        
        for cookie_name, cookie_value in results.get('session_cookies', {}).items():
            display_val = cookie_value[:30] + "..." if len(str(cookie_value)) > 30 else cookie_value
            report += f"│    • {cookie_name}: {display_val}\n"
        
        report += f"""│
└───────────────────────────────────────────────────────────────────────────┘

NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Update .env.algosense with the discovered endpoint details:
   
   ALGOSENSE_API_LOGIN_URL={results.get('login_endpoint', {}).get('url', '')}
   ALGOSENSE_API_LOGIN_METHOD={results.get('login_endpoint', {}).get('method', 'POST')}

2. Verify the request fields match your form fields

3. Rerun algosense_auto_login.py with the new configuration

Full log saved to: algosense_api_discovery.log

═══════════════════════════════════════════════════════════════════════════════
"""
        
        logger.info(report)
        return report

def main():
    """Main execution"""
    discovery = AlgosenseAPIDiscovery()
    results = discovery.capture_login_requests()
    
    if results:
        report = discovery.generate_report(results)
        
        # Save results as JSON
        with open('algosense_api_discovery.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n[Discovery] Results saved to algosense_api_discovery.json")
        
        return True
    else:
        logger.error("\n[Discovery] ❌ Failed to discover API endpoints")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
