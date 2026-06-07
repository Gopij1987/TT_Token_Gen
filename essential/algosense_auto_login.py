"""
Algosense Auto Login - Pure API Version (no browser required)
Fast, reliable, and lightweight authentication

API Endpoint: POST https://api.algotest.in/login
Payload Format: {"phoneNumber": "+91XXXXXXXXXX", "password": "..."}

Usage:
  python algosense_auto_login.py
"""
import os
import sys
import json
import time
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
logger = logging.getLogger('ALGOSENSE')

# Load environment variables
dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)


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
            message = f"""<b>✅ Algosense Login Successful</b>
👤 Account: <code>{username}</code>
⏰ Time: <code>{timestamp}</code>
⏳ Duration: <code>{duration:.1f}s</code>
🖥️ Type: <code>Pure API</code>"""
        else:
            message = f"""<b>❌ Algosense Login Failed</b>
👤 Account: <code>{username}</code>
⏰ Time: <code>{timestamp}</code>
❌ Error: <code>{error_msg}</code>"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        requests.post(url, json=payload, timeout=5)
    except:
        pass


class AlgosenseAutoLogin:
    """Algosense API-based login (no browser required)"""
    
    def __init__(self):
        self.api_base = "https://api.algotest.in"
        self.login_endpoint = f"{self.api_base}/login"
        self.tag = "ALGOSENSE"
        self.session = requests.Session()
        
        # Browser-like headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://algotest.in',
            'Referer': 'https://algotest.in/login',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        })

    def login(self) -> bool:
        """Perform API login"""
        
        username = os.getenv('ALGOSENSE_USERNAME')
        password = os.getenv('ALGOSENSE_PASSWORD')
        
        if not username or not password:
            logger.error(f"[{self.tag}] ❌ Missing credentials in .env.algosense")
            return False
        
        # Format phone: ensure +91 prefix
        phone = str(username).strip()
        if not phone.startswith('+91'):
            phone = phone.lstrip('0')
            phone = f"+91{phone}"
        
        start_time = time.time()
        
        try:
            logger.info("\n" + "="*70)
            logger.info(f"[{self.tag}] ALGOSENSE AUTO LOGIN - PURE API")
            logger.info("="*70)
            
            # STEP 1: Prepare request
            logger.info(f"\n[{self.tag}] STEP 1: Preparing login request...")
            logger.info(f"[{self.tag}] Endpoint: POST {self.login_endpoint}")
            logger.info(f"[{self.tag}] Username: {username}")
            
            payload = {
                "phoneNumber": phone,
                "password": password
            }
            
            # STEP 2: Send request
            logger.info(f"\n[{self.tag}] STEP 2: Sending login request...")
            
            response = self.session.post(
                self.login_endpoint,
                json=payload,
                timeout=30,
                allow_redirects=True
            )
            
            logger.info(f"[{self.tag}] Response Status: {response.status_code}")
            
            # STEP 3: Validate response
            logger.info(f"\n[{self.tag}] STEP 3: Validating response...")
            
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}"
                logger.error(f"[{self.tag}] ❌ Login failed: {error_msg}")
                try:
                    error_data = response.json()
                    logger.error(f"[{self.tag}] Error: {error_data}")
                except:
                    pass
                send_telegram_notification('error', username, error_msg=error_msg)
                return False
            
            # Parse response
            try:
                result = response.json()
                
                if result.get('login') is True:
                    logger.info(f"[{self.tag}] ✓ Login confirmed")
                    if 'data' in result:
                        user_data = result['data']
                        logger.info(f"[{self.tag}] User: {user_data.get('username', 'N/A')}")
                        
            except Exception as e:
                logger.warning(f"[{self.tag}] Could not parse response: {e}")
            
            # STEP 4: Extract cookies
            logger.info(f"\n[{self.tag}] STEP 4: Extracting session info...")
            
            cookies = {}
            for name, value in self.session.cookies.items():
                cookies[name] = value
                if 'token' in name.lower():
                    logger.info(f"[{self.tag}] ✓ Cookie: {name}")
            
            logger.info(f"[{self.tag}] Total cookies: {len(cookies)}")
            
            # SUCCESS
            duration = time.time() - start_time
            
            logger.info(f"\n[{self.tag}] " + "="*68)
            logger.info(f"[{self.tag}] ✅✅✅ LOGIN SUCCESSFUL ✅✅✅")
            logger.info(f"[{self.tag}] " + "="*68)
            logger.info(f"[{self.tag}] Duration: {duration:.1f} seconds")
            logger.info(f"[{self.tag}] Cookies: {len(cookies)}")
            
            # Save session
            session_file = Path(__file__).parent / '.algosense_session.json'
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'endpoint': self.login_endpoint,
                'method': 'POST',
                'status_code': response.status_code,
                'cookies': {k: v[:50] + "..." if len(str(v)) > 50 else v for k, v in cookies.items()},
                'duration_seconds': duration
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"[{self.tag}] Session saved to: {session_file}")
            
            # Send notification
            send_telegram_notification('success', username, duration)
            
            return True
            
        except requests.Timeout:
            error_msg = "Request timeout (30 sec)"
            logger.error(f"[{self.tag}] ❌ {error_msg}")
            send_telegram_notification('error', username, error_msg=error_msg)
            return False
        except Exception as e:
            error_msg = f"Login error: {str(e)[:100]}"
            logger.error(f"[{self.tag}] ❌ {error_msg}")
            send_telegram_notification('error', username, error_msg=error_msg)
            return False


def main():
    """Main"""
    login = AlgosenseAutoLogin()
    return login.login()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[ALGOSENSE] Interrupted")
        sys.exit(1)
