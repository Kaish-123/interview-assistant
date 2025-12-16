#!/bin/bash
# Stop TechyEra Web Dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping TechyEra Web Dashboard..."

# Kill by PID file
if [ -f ".server.pid" ]; then
    PID=$(cat .server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "   Stopped process $PID"
    fi
    rm -f .server.pid
fi

# Kill any remaining uvicorn processes for this app
pkill -f "uvicorn.*app:app" 2>/dev/null

rm -f .server.port

echo "✅ Server stopped!"

