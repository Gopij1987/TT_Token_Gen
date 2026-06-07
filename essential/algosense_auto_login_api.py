"""
Algosense Auto Login - Pure API Version
No browser required - uses direct API calls

Usage:
  python algosense_auto_login_api.py

Requirements:
  pip install requests python-dotenv
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
logger = logging.getLogger('ALGOSENSE-API')

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
            message = f"""
<b>✅ Algosense Login Successful</b>
👤 Account: <code>{username}</code>
⏰ Time: <code>{timestamp}</code>
⏳ Duration: <code>{duration:.1f}s</code>
🖥️ Type: <code>Pure API (No Browser)</code>
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


class AlgosenseAPILogin:
    """Pure API-based login for Algosense"""
    
    def __init__(self):
        self.api_base = "https://api.algotest.in"
        self.login_endpoint = f"{self.api_base}/login"
        self.session = requests.Session()
        self.tag = "ALGOSENSE-API"
        
        # Set headers to mimic browser
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
        
        # Format phone number: ensure +91 prefix
        phone_number = str(username).strip()
        if not phone_number.startswith('+91'):
            # Remove leading 0 if present
            phone_number = phone_number.lstrip('0')
            # Add +91 prefix
            phone_number = f"+91{phone_number}"
        
        logger.info(f"[{self.tag}] Phone formatted: {phone_number}")
        
        start_time = time.time()
        
        try:
            logger.info("\n" + "="*70)
            logger.info(f"[{self.tag}] ALGOSENSE AUTO LOGIN - PURE API")
            logger.info("="*70)
            
            # STEP 1: Try JSON payload with phone/password
            logger.info(f"\n[{self.tag}] STEP 1: Attempting login with JSON payload...")
            logger.info(f"[{self.tag}] Endpoint: POST {self.login_endpoint}")
            logger.info(f"[{self.tag}] Username: {username}")
            
            # Try different payload formats
            payloads = [
                # Format 1: phoneNumber + password (CORRECT FORMAT)
                {
                    "phoneNumber": phone_number,
                    "password": password
                },
                # Format 2: phone + password
                {
                    "phone": phone_number,
                    "password": password
                },
                # Format 3: username + password
                {
                    "username": phone_number,
                    "password": password
                },
            ]
            
            auth_response = None
            payload_used = None
            
            for i, payload in enumerate(payloads, 1):
                try:
                    logger.info(f"\n[{self.tag}] Trying format {i}: {list(payload.keys())}")
                    
                    response = self.session.post(
                        self.login_endpoint,
                        json=payload,
                        timeout=30,
                        allow_redirects=True
                    )
                    
                    logger.info(f"[{self.tag}] Status: {response.status_code}")
                    
                    # Log response
                    try:
                        resp_data = response.json()
                        logger.info(f"[{self.tag}] Response: {json.dumps(resp_data, indent=2)[:200]}")
                        
                        # Check for success indicators
                        if response.status_code in [200, 201]:
                            if any(k in resp_data for k in ['token', 'access_token', 'success', 'data']):
                                auth_response = response
                                payload_used = payload
                                logger.info(f"[{self.tag}] ✅ Found valid response format!")
                                break
                    except:
                        # Response is not JSON
                        logger.info(f"[{self.tag}] Response: {response.text[:100]}")
                        
                        if response.status_code in [200, 201]:
                            auth_response = response
                            payload_used = payload
                            logger.info(f"[{self.tag}] ✅ Valid status code!")
                            break
                    
                except Exception as e:
                    logger.warning(f"[{self.tag}] Format {i} failed: {str(e)[:50]}")
                    continue
            
            if not auth_response:
                error_msg = "All payload formats failed"
                logger.error(f"[{self.tag}] ❌ {error_msg}")
                send_telegram_notification('error', username, error_msg=error_msg)
                return False
            
            logger.info(f"\n[{self.tag}] ✅ Login successful with format: {list(payload_used.keys())}")
            
            # STEP 2: Extract token from response
            logger.info(f"\n[{self.tag}] STEP 2: Extracting authentication tokens...")
            
            tokens = {}
            cookies = {}
            
            # Check response body
            try:
                resp_data = auth_response.json()
                logger.info(f"[{self.tag}] Response keys: {list(resp_data.keys())}")
                
                # Look for token in various fields
                for key in ['token', 'access_token', 'accessToken', 'auth_token', 'authToken', 'data']:
                    if key in resp_data:
                        value = resp_data[key]
                        if isinstance(value, dict):
                            for k, v in value.items():
                                if 'token' in k.lower():
                                    tokens[k] = v
                                    logger.info(f"[{self.tag}] ✓ Found token: {k}")
                        else:
                            tokens[key] = value
                            logger.info(f"[{self.tag}] ✓ Token: {key}")
                        
                        # Check if data contains token
                        if key == 'data' and isinstance(value, dict):
                            for k, v in value.items():
                                if 'token' in k.lower():
                                    tokens[k] = v
                                    logger.info(f"[{self.tag}] ✓ Found token in data: {k}")
                
            except Exception as e:
                logger.warning(f"[{self.tag}] Could not parse response JSON: {e}")
            
            # Check response headers for cookies
            for cookie_name, cookie_value in auth_response.cookies.items():
                cookies[cookie_name] = cookie_value
                if 'token' in cookie_name.lower() or 'session' in cookie_name.lower():
                    logger.info(f"[{self.tag}] ✓ Cookie: {cookie_name}")
            
            # Check for Set-Cookie headers
            if 'Set-Cookie' in auth_response.headers:
                logger.info(f"[{self.tag}] ✓ Set-Cookie header found")
            
            # STEP 3: Verify session establishment
            logger.info(f"\n[{self.tag}] STEP 3: Verifying session...")
            
            try:
                # Try to access a protected endpoint
                user_endpoint = f"{self.api_base}/user"
                user_response = self.session.get(user_endpoint, timeout=10)
                
                if user_response.status_code == 200:
                    logger.info(f"[{self.tag}] ✓ Session verified - can access /user endpoint")
                    user_data = user_response.json()
                    logger.info(f"[{self.tag}] User data: {list(user_data.keys())}")
                else:
                    logger.warning(f"[{self.tag}] ⚠️  /user endpoint status: {user_response.status_code}")
                    
            except Exception as e:
                logger.warning(f"[{self.tag}] Could not verify session: {e}")
            
            # SUCCESS
            duration = time.time() - start_time
            
            logger.info(f"\n[{self.tag}] " + "="*68)
            logger.info(f"[{self.tag}] ✅✅✅ LOGIN SUCCESSFUL ✅✅✅")
            logger.info(f"[{self.tag}] " + "="*68)
            logger.info(f"[{self.tag}] Duration: {duration:.1f} seconds")
            logger.info(f"[{self.tag}] Endpoint: {self.login_endpoint}")
            logger.info(f"[{self.tag}] Tokens found: {len(tokens)}")
            logger.info(f"[{self.tag}] Cookies: {len(cookies)}")
            
            # Save session
            session_file = Path(__file__).parent / '.algosense_session_api.json'
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'endpoint': self.login_endpoint,
                'payload_format': list(payload_used.keys()),
                'tokens': {k: v[:50] + "..." if len(str(v)) > 50 else v for k, v in tokens.items()},
                'cookies': {k: v[:50] + "..." if len(str(v)) > 50 else v for k, v in cookies.items()},
                'duration_seconds': duration
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"[{self.tag}] Session saved to: {session_file}")
            
            # Send notification
            send_telegram_notification('success', username, duration)
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.tag}] ❌ Login error: {e}", exc_info=True)
            send_telegram_notification('error', username, error_msg=str(e)[:100])
            return False


def main():
    """Main execution"""
    login = AlgosenseAPILogin()
    success = login.login()
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[ALGOSENSE-API] Interrupted by user")
        sys.exit(1)
