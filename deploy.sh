#!/bin/bash
# Oracle AI Trading Hub - Live Deployment Script
# Usage: ./deploy.sh <deployment_name> [symbols...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="$SCRIPT_DIR"

# Default values
DEPLOYMENT_NAME="${1:-test-deployment}"
shift || true
SYMBOLS="${@:-BTC/USDT ETH/USDT}"

echo "=============================================="
echo "Oracle AI Trading Hub - Live Deployment"
echo "=============================================="
echo "Deployment: $DEPLOYMENT_NAME"
echo "Symbols: $SYMBOLS"
echo "=============================================="

# Check .env file
if [ ! -f .env ]; then
    echo "WARNING: .env file not found. Creating from example..."
    cp .env.example .env
    echo "Please configure API keys in .env before running live."
    exit 1
fi

# Initialize database
python3 -c "from core.database import init_db; init_db()"

# Run live trading
echo "Starting live trading..."
python3 main.py live "$DEPLOYMENT_NAME" $SYMBOLS
