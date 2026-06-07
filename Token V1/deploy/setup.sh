#!/bin/bash
# VPS one-time setup for Token V1
# Run as root after copying Token V1/ to /opt/token-v1/

set -e

echo "=== Token V1 VPS Setup ==="

APP_DIR="/opt/token-v1"
VENV_DIR="/opt/token-v1/venv"
LOG_DIR="/var/log/token-v1"

# Create directories
mkdir -p "$APP_DIR"
mkdir -p "$LOG_DIR"

# Install system dependencies (Debian/Ubuntu)
if command -v apt-get &> /dev/null; then
    echo "Installing system deps..."
    apt-get update
    apt-get install -y python3 python3-venv python3-pip wget gnupg unzip
    
    # Chrome + ChromeDriver
    echo "Installing Chrome..."
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
    apt-get install -y google-chrome-stable
    
    # ChromeDriver (match Chrome version)
    echo "Installing ChromeDriver..."
    CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%.*}")
    wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip
    unzip -q /tmp/chromedriver.zip -d /usr/local/bin/
    chmod +x /usr/local/bin/chromedriver
    rm /tmp/chromedriver.zip
fi

# Create virtual environment
echo "Creating Python venv..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install Python deps
echo "Installing Python deps..."
pip install --upgrade pip
pip install selenium pyotp requests python-dotenv

# Touch log files
touch "$LOG_DIR/gj114.log" "$LOG_DIR/pp450.log" "$LOG_DIR/rr1001.log"
chmod 666 "$LOG_DIR"/*.log

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Add cron jobs: sudo crontab -e"
echo "  2. Paste these 3 lines:"
echo "     31 8 * * 1-5 TZ=Asia/Kolkata $VENV_DIR/bin/python3 $APP_DIR/token_automation.py --account GJ114 >> $LOG_DIR/gj114.log 2>&1"
echo "     31 8 * * 1-5 TZ=Asia/Kolkata $VENV_DIR/bin/python3 $APP_DIR/token_automation.py --account PP450 >> $LOG_DIR/pp450.log 2>&1"
echo "     31 8 * * 1-5 TZ=Asia/Kolkata $VENV_DIR/bin/python3 $APP_DIR/token_automation.py --account RR1001 >> $LOG_DIR/rr1001.log 2>&1"
echo ""
echo "  3. Test accounts:"
echo "     $VENV_DIR/bin/python3 $APP_DIR/token_automation.py --account GJ114"
echo ""
echo "  4. View logs:"
echo "     tail -f $LOG_DIR/*.log"
echo ""
echo "  5. Update TT Wallet bot with Token V1 commands:"
echo "     (Copy extended telegram_bot.py to VPS and restart)"
