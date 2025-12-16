#!/bin/bash
# TechyEra Telegram Marketing - Web Dashboard Startup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     TechyEra Telegram Marketing - Web Dashboard            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -r requirements.txt --quiet

# Find available port
find_port() {
    local port=$1
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

PORT=$(find_port 8888)

echo ""
echo -e "${GREEN}✅ Starting server on port $PORT${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "   🌐 Dashboard URL: ${GREEN}http://localhost:$PORT${NC}"
echo -e "   📱 Network URL:   ${GREEN}http://$(ipconfig getifaddr en0 2>/dev/null || echo "your-ip"):$PORT${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server
python3 -c "import uvicorn; uvicorn.run('app:app', host='0.0.0.0', port=$PORT, reload=False)"

