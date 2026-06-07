"""
Algosense API Endpoint Discovery - Enhanced with Network Monitoring
Uses Chrome DevTools Protocol to capture login API calls

pip install selenium webdriver-manager
"""
import os
import json
import sys
import time
import base64
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

dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    logger.error("❌ Selenium not installed. Install with: pip install selenium webdriver-manager")
    sys.exit(1)

class NetworkMonitor:
    """Monitor network requests using CDP"""
    
    def __init__(self, driver):
        self.driver = driver
        self.requests = []
        self.responses = {}
        
    def start_monitoring(self):
        """Start monitoring network requests"""
        try:
            # Enable network tracking
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            logger.info("[CDP] Network monitoring enabled")
        except Exception as e:
            logger.warning(f"[CDP] Could not enable full network monitoring: {e}")
    
    def get_network_logs(self) -> List[Dict[str, Any]]:
        """Get network logs from CDP"""
        try:
            # Get network activity from browser logs
            logs = self.driver.get_log('performance')
            return logs
        except:
            return []
    
    def get_requests_from_devtools(self) -> List[Dict[str, Any]]:
        """Extract captured requests"""
        captured = []
        try:
            # Try to get fetch/XHR information
            script = """
            return window.__captured_requests__ || [];
            """
            captured = self.driver.execute_script(script)
        except:
            pass
        return captured if isinstance(captured, list) else []

class AlgosenseAdvancedDiscovery:
    """Advanced API discovery with network monitoring"""
    
    def __init__(self):
        self.base_url = "https://algotest.in"
        self.login_url = f"{self.base_url}/login"
        self.tag = "ADVANCED-DISCOVERY"
        self.driver = None
        self.discovered_endpoints = []

    def setup_selenium(self):
        """Setup Selenium with CDP"""
        try:
            logger.info(f"[{self.tag}] Setting up Selenium WebDriver...")
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-notifications')
            
            # Enable CDP/performance logging
            chrome_options.set_capability('goog:loggingPrefs', {
                'performance': 'ALL',
                'browser': 'INFO'
            })
            
            logger.info(f"[{self.tag}] Starting Chrome WebDriver...")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            self.driver.set_script_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info(f"[{self.tag}] ✓ WebDriver ready")
            return True
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ Setup failed: {e}")
            return False

    def inject_request_interceptor(self):
        """Inject JavaScript to intercept fetch/XHR calls"""
        script = """
        // Store captured requests
        window.__captured_requests__ = [];
        
        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = typeof args[0] === 'string' ? args[0] : args[0].url;
            const method = (args[1]?.method || 'GET').toUpperCase();
            const body = args[1]?.body || '';
            
            // Log request details
            if (url.includes('algotest') || url.includes('api')) {
                console.log(`FETCH: ${method} ${url}`);
                window.__captured_requests__.push({
                    type: 'fetch',
                    method: method,
                    url: url,
                    timestamp: new Date().toISOString()
                });
            }
            
            return originalFetch.apply(this, args).then(response => {
                return response;
            });
        };
        
        // Intercept XMLHttpRequest
        const XHROpen = XMLHttpRequest.prototype.open;
        const XHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url) {
            this.__method__ = method;
            this.__url__ = url;
            
            if (url.includes('algotest') || url.includes('api')) {
                console.log(`XHR: ${method} ${url}`);
            }
            
            return XHROpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function(body) {
            const method = this.__method__ || 'GET';
            const url = this.__url__ || '';
            
            if (url.includes('algotest') || url.includes('api')) {
                window.__captured_requests__.push({
                    type: 'xhr',
                    method: method,
                    url: url,
                    timestamp: new Date().toISOString()
                });
            }
            
            return XHRSend.apply(this, arguments);
        };
        
        console.log('Request interceptor installed');
        """
        
        try:
            self.driver.execute_script(script)
            logger.info(f"[{self.tag}] Request interceptor injected")
            return True
        except Exception as e:
            logger.warning(f"[{self.tag}] Could not inject interceptor: {e}")
            return False

    def discover_endpoints(self) -> Dict[str, Any]:
        """Discover API endpoints"""
        
        username = os.getenv('ALGOSENSE_USERNAME')
        password = os.getenv('ALGOSENSE_PASSWORD')
        
        try:
            logger.info(f"\n[{self.tag}] Step 1: Opening login page...")
            self.driver.get(self.login_url)
            time.sleep(2)
            
            # Inject interceptor
            self.inject_request_interceptor()
            time.sleep(1)
            
            logger.info(f"[{self.tag}] Step 2: Filling credentials...")
            
            # Find and fill username
            try:
                username_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="text"]')
                username_field.clear()
                username_field.send_keys(username)
                logger.info(f"[{self.tag}] Username filled")
            except Exception as e:
                logger.error(f"[{self.tag}] Could not fill username: {e}")
                return {}
            
            # Find and fill password
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                password_field.clear()
                password_field.send_keys(password)
                logger.info(f"[{self.tag}] Password filled")
            except Exception as e:
                logger.error(f"[{self.tag}] Could not fill password: {e}")
                return {}
            
            logger.info(f"[{self.tag}] Step 3: Clicking login button...")
            
            # Find and click login button
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                login_button = None
                for btn in buttons:
                    if 'login' in btn.text.lower() or 'sign' in btn.text.lower():
                        login_button = btn
                        break
                
                if not login_button and buttons:
                    login_button = buttons[0]  # Try first button
                
                if login_button:
                    login_button.click()
                    logger.info(f"[{self.tag}] Login button clicked")
                else:
                    logger.error(f"[{self.tag}] Could not find login button")
                    return {}
                    
            except Exception as e:
                logger.error(f"[{self.tag}] Error clicking button: {e}")
                return {}
            
            logger.info(f"[{self.tag}] Step 4: Waiting for login response...")
            time.sleep(5)
            
            logger.info(f"[{self.tag}] Step 5: Extracting captured requests...")
            
            # Get captured requests
            captured_requests = self.driver.execute_script("return window.__captured_requests__ || [];")
            logger.info(f"[{self.tag}] Captured {len(captured_requests)} requests")
            
            for req in captured_requests:
                logger.info(f"  • {req.get('method', 'GET')} {req.get('url', 'N/A')}")
                if '/api/' in req.get('url', '') or '/login' in req.get('url', ''):
                    self.discovered_endpoints.append(req)
            
            # Get Chrome DevTools Protocol logs
            logger.info(f"[{self.tag}] Step 6: Extracting CDP performance logs...")
            
            try:
                perf_logs = self.driver.get_log('performance')
                api_endpoints = []
                
                for log in perf_logs:
                    try:
                        message = json.loads(log['message'])['message']
                        
                        if message['method'] == 'Network.responseReceived':
                            params = message['params']
                            if 'response' in params:
                                url = params['response'].get('url', '')
                                method = params['response'].get('requestHeaders', {}).get(':method', 'GET')
                                status = params['response'].get('status', 0)
                                
                                if '/api/' in url or '/login' in url:
                                    api_endpoints.append({
                                        'url': url,
                                        'status': status,
                                        'method': method
                                    })
                                    logger.info(f"  • [CDP] {method} {url} ({status})")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"[{self.tag}] Could not get CDP logs: {e}")
            
            # Final state
            final_url = self.driver.current_url
            logger.info(f"[{self.tag}] Final URL: {final_url}")
            
            # Extract all cookies
            cookies = {}
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value'][:50] + "..." if len(cookie.get('value', '')) > 50 else cookie.get('value', '')
            
            discovery = {
                'timestamp': datetime.now().isoformat(),
                'final_url': final_url,
                'captured_requests': captured_requests,
                'discovered_endpoints': self.discovered_endpoints,
                'cookies': cookies,
                'success': 'dashboard' in final_url.lower() or 'success' in final_url.lower()
            }
            
            return discovery
            
        except Exception as e:
            logger.error(f"[{self.tag}] Error: {e}", exc_info=True)
            return {}
        finally:
            if self.driver:
                self.driver.quit()

    def generate_report(self, results: Dict[str, Any]):
        """Generate report"""
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║            ALGOSENSE ADVANCED API DISCOVERY REPORT                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

Timestamp: {results.get('timestamp', 'N/A')}
Login Success: {'✅ YES' if results.get('success') else '❌ NO'}
Final URL: {results.get('final_url', 'N/A')}

CAPTURED NETWORK REQUESTS:
─────────────────────────────────────────────────────────────────────────────
"""
        
        for req in results.get('captured_requests', []):
            report += f"  {req.get('type', 'UNKNOWN').upper()}: {req.get('method', 'GET')} {req.get('url', 'N/A')}\n"
        
        report += f"""
DISCOVERED API ENDPOINTS:
─────────────────────────────────────────────────────────────────────────────
"""
        
        endpoints = results.get('discovered_endpoints', [])
        if endpoints:
            for ep in endpoints:
                report += f"  • {ep.get('method', 'GET')} {ep.get('url', 'N/A')}\n"
        else:
            report += "  (No API endpoints found - try checking DevTools Network tab manually)\n"
        
        report += f"""
SESSION COOKIES ({len(results.get('cookies', {}))}):
─────────────────────────────────────────────────────────────────────────────
"""
        
        for name, value in results.get('cookies', {}).items():
            if name in ['access_token_cookie', 'csrf_access_token', 'authorization']:
                report += f"  🔑 {name}: {value}\n"
        
        report += f"""
═══════════════════════════════════════════════════════════════════════════════

IMPORTANT:
If no API endpoints are shown above, the login form likely submits directly
without a separate API call. The success can still be verified by:
  ✓ Redirect to /dashboard (success)
  ✓ access_token_cookie set
  ✓ Session established

═══════════════════════════════════════════════════════════════════════════════
"""
        
        logger.info(report)

def main():
    """Main"""
    logger.info("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                   ALGOSENSE ADVANCED API DISCOVERY                       ║
║            Network Monitoring with Chrome DevTools Protocol              ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    discovery = AlgosenseAdvancedDiscovery()
    
    if not discovery.setup_selenium():
        return False
    
    results = discovery.discover_endpoints()
    discovery.generate_report(results)
    
    if results:
        with open('algosense_advanced_discovery.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("\n✓ Results saved to algosense_advanced_discovery.json")
    
    return bool(results.get('success', False))

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted")
        sys.exit(1)
