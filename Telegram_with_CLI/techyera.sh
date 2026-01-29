#!/bin/bash
# TechyEra Telegram Marketing CLI
# Usage: ./techyera.sh [command]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use python3 explicitly
PYTHON="python3"

show_help() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║         TechyEra Telegram Marketing CLI                ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo "Usage: ./techyera.sh [command]"
    echo ""
    echo "Commands:"
    echo "  status    - Show bot status and stats"
    echo "  send      - Send messages now"
    echo "  grow      - Run group growth now"
    echo "  groups    - List all target groups"
    echo "  logs      - Show recent logs"
    echo "  errors    - Show recent errors"
    echo "  next      - Show next scheduled runs"
    echo "  start     - Start automation (load LaunchAgents)"
    echo "  stop      - Stop automation (unload LaunchAgents)"
    echo "  help      - Show this help"
    echo ""
}

case "$1" in
    status)
        $PYTHON monitor.py --stats
        ;;
    send)
        echo "📨 Sending messages now..."
        $PYTHON cron_send_messages.py
        ;;
    grow)
        echo "🌱 Running growth now..."
        $PYTHON cron_growth.py
        ;;
    groups)
        $PYTHON -c "
import json
with open('config.json') as f:
    config = json.load(f)
print()
print('📋 TARGET GROUPS')
print('=' * 50)
for i, t in enumerate(config['targets'], 1):
    status = '✓' if t.get('enabled', True) else '✗'
    source = f\" [{t.get('source', 'manual')}]\" if t.get('source') else ''
    print(f'{i:3}. {status} @{t[\"username\"]}{source}')
print()
print(f'Total: {len(config[\"targets\"])} groups')
"
        ;;
    logs)
        $PYTHON monitor.py --logs --lines 30
        ;;
    errors)
        $PYTHON monitor.py --errors
        ;;
    next)
        $PYTHON next_run.py
        ;;
    start)
        echo "🚀 Starting automation..."
        launchctl load ~/Library/LaunchAgents/com.techyera.telegram.send.plist 2>/dev/null
        launchctl load ~/Library/LaunchAgents/com.techyera.telegram.growth.plist 2>/dev/null
        echo "✓ Automation started"
        launchctl list | grep techyera
        ;;
    stop)
        echo "🛑 Stopping automation..."
        launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.send.plist 2>/dev/null
        launchctl unload ~/Library/LaunchAgents/com.techyera.telegram.growth.plist 2>/dev/null
        echo "✓ Automation stopped"
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        ;;
esac
