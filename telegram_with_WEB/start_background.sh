#!/bin/bash
# Start TechyEra Web Dashboard in background

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if already running
if pgrep -f "uvicorn.*app:app" > /dev/null; then
    echo "⚠️  Server is already running!"
    echo "   To stop: ./stop.sh"
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
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

# Start in background
nohup python3 -c "import uvicorn; uvicorn.run('app:app', host='0.0.0.0', port=$PORT)" > server.log 2>&1 &

echo $! > .server.pid
echo $PORT > .server.port

sleep 2

if pgrep -f "uvicorn.*app:app" > /dev/null; then
    echo "✅ Server started successfully!"
    echo ""
    echo "🌐 Dashboard: http://localhost:$PORT"
    echo ""
    echo "📋 Commands:"
    echo "   View logs: tail -f server.log"
    echo "   Stop:      ./stop.sh"
else
    echo "❌ Failed to start server. Check server.log for details."
fi

