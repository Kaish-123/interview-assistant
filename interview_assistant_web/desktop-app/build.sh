#!/bin/bash
# Build script for Interview Assistant Desktop App

set -e

echo "🚀 Building Interview Assistant Desktop App..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DESKTOP_DIR="$SCRIPT_DIR"

echo -e "${YELLOW}Project directory: $PROJECT_DIR${NC}"

# Step 1: Install desktop app dependencies
echo -e "\n${GREEN}Step 1: Installing desktop app dependencies...${NC}"
cd "$DESKTOP_DIR"
npm install

# Step 2: Build frontend
echo -e "\n${GREEN}Step 2: Building frontend...${NC}"
cd "$FRONTEND_DIR"
npm install
npm run build

# Step 3: Build backend (create standalone executable)
echo -e "\n${GREEN}Step 3: Building backend...${NC}"
cd "$BACKEND_DIR"

# Install PyInstaller if not present
pip3 install pyinstaller --quiet

# Create standalone backend
echo "Creating standalone Python backend..."
pyinstaller --onedir \
    --name backend \
    --add-data "database:database" \
    --add-data "services:services" \
    --add-data "routes:routes" \
    --add-data "models:models" \
    --hidden-import=uvicorn \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.protocols \
    --hidden-import=uvicorn.protocols.http \
    --hidden-import=uvicorn.protocols.http.auto \
    --hidden-import=uvicorn.protocols.websockets \
    --hidden-import=uvicorn.protocols.websockets.auto \
    --hidden-import=uvicorn.lifespan \
    --hidden-import=uvicorn.lifespan.on \
    --hidden-import=openai \
    --hidden-import=sqlalchemy \
    --hidden-import=pydantic \
    --hidden-import=websockets \
    --hidden-import=aiofiles \
    --collect-all openai \
    --collect-all sqlalchemy \
    main.py

# Step 4: Build Electron app
echo -e "\n${GREEN}Step 4: Building Electron app...${NC}"
cd "$DESKTOP_DIR"

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Building for macOS..."
    npm run build:mac
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Building for Windows..."
    npm run build:win
else
    echo "Building for current platform..."
    npm run dist
fi

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "Output is in: $DESKTOP_DIR/dist/"
ls -la "$DESKTOP_DIR/dist/"


