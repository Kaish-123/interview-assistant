#!/bin/bash

# Interview Assistant Web - Start Script
# This script starts both the backend and frontend servers

echo "🚀 Starting Interview Assistant Web..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check for --with-hotkeys flag
WITH_HOTKEYS=false
for arg in "$@"; do
    if [ "$arg" == "--with-hotkeys" ] || [ "$arg" == "-h" ]; then
        WITH_HOTKEYS=true
    fi
done

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $HOTKEYS_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo "📦 Starting Backend Server..."
cd "$SCRIPT_DIR/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "Please create backend/.env with your OPENAI_API_KEY"
    echo "Example:"
    echo "  OPENAI_API_KEY=sk-your-api-key-here"
    exit 1
fi

# Start backend in background
python main.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 3

# Start Frontend
echo "📦 Starting Frontend Server..."
cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

# Start Global Hotkey Listener if requested
if [ "$WITH_HOTKEYS" = true ]; then
    echo ""
    echo "🎹 Starting Global Hotkey Listener..."
    cd "$SCRIPT_DIR"
    
    # Install hotkey dependencies if needed
    pip install pynput requests websocket-client 2>/dev/null
    
    # Start hotkey listener in background
    python global_hotkeys.py &
    HOTKEYS_PID=$!
    echo "✅ Global Hotkeys started (PID: $HOTKEYS_PID)"
fi

echo ""
echo "=========================================="
echo "🎉 Interview Assistant Web is running!"
echo "=========================================="
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
if [ "$WITH_HOTKEYS" = true ]; then
    echo "🎹 Global Hotkeys: ACTIVE"
fi
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for any process to exit
wait

