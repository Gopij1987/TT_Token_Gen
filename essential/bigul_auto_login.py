"""
Bigul Broker Auto-Login
Logs into Bigul XTS broker using the discovered API endpoint
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('BIGUL-LOGIN')

dotenv_path = Path(__file__).parent.parent / '.env.algosense'
load_dotenv(dotenv_path)

# Bigul API Configuration
BIGUL_BROKER_ID = "692ffb6227b32fdf02615607"  # Bigul XTS Broker ID
BIGUL_LOGIN_URL = f"https://api.algotest.in/broker_login/xts_confirm/{BIGUL_BROKER_ID}"
ALGOSENSE_SESSION_FILE = Path(__file__).parent / '.algosense_session.json'


def load_session():
    """Load existing Algosense session"""
    if ALGOSENSE_SESSION_FILE.exists():
        with open(ALGOSENSE_SESSION_FILE, 'r') as f:
            return json.load(f)
    return None


def bigul_login():
    """Login to Bigul broker using API"""
    
    logger.info("\n" + "="*80)
    logger.info("BIGUL BROKER AUTO-LOGIN")
    logger.info("="*80)
    
    # Check for existing session
    logger.info("\n[STEP 1] Checking for existing Algosense session...")
    session_data = load_session()
    
    if not session_data:
        logger.error("❌ No Algosense session found!")
        logger.info("   Please run Algosense login first: python algosense_auto_login.py")
        return False
    
    logger.info(f"✓ Algosense session loaded")
    logger.info(f"  User: {session_data.get('username', 'Unknown')}")
    logger.info(f"  Logged in: {session_data.get('login', False)}")
    
    # Extract CSRF token
    csrf_token = session_data.get('csrf_token')
    if not csrf_token:
        logger.error("❌ CSRF token not found in session!")
        return False
    
    logger.info(f"✓ CSRF token found: {csrf_token[:20]}...")
    
    # Log into Bigul
    logger.info("\n[STEP 2] Logging into Bigul broker...")
    logger.info(f"  Endpoint: POST {BIGUL_LOGIN_URL}")
    
    try:
        response = requests.post(
            BIGUL_LOGIN_URL,
            json={},  # Bigul endpoint expects empty body
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "X-CSRF-TOKEN-ACCESS": csrf_token,
                "Referer": "https://algotest.in/broker",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=30
        )
        
        logger.info(f"\n  Status Code: {response.status_code}")
        logger.info(f"  Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'location', 'set-cookie']:
                logger.info(f"    {key}: {value}")
        
        # Try to parse response as JSON
        try:
            response_data = response.json()
            logger.info(f"\n  Response Body:")
            logger.info(f"    {json.dumps(response_data, indent=2)}")
        except:
            logger.info(f"\n  Response Text: {response.text[:200]}")
        
        if response.status_code == 200:
            logger.info("\n✅ BIGUL LOGIN SUCCESSFUL!")
            
            # Save response to file
            response_file = Path(__file__).parent / 'bigul_login_response.json'
            with open(response_file, 'w') as f:
                try:
                    f.write(json.dumps(response.json(), indent=2))
                except:
                    f.write(response.text)
            logger.info(f"  Response saved to: {response_file}")
            
            return True
        else:
            logger.error(f"\n❌ Login failed with status {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = bigul_login()
        
        if success:
            logger.info("\n" + "="*80)
            logger.info("✅ BIGUL LOGIN COMPLETE - Ready for trading")
            logger.info("="*80)
            sys.exit(0)
        else:
            logger.info("\n" + "="*80)
            logger.info("❌ BIGUL LOGIN FAILED")
            logger.info("="*80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
