#!/bin/bash
# TechyEra Marketing Bot - Quick Command Tool
# Usage: ./techyera.sh [command]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Always use the virtual environment python
PYTHON="$SCRIPT_DIR/venv/bin/python3"

show_help() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║       📱 TECHYERA TELEGRAM MARKETING BOT                 ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Usage: ./techyera.sh [command]"
    echo ""
    echo "Commands:"
    echo "  status    - Check if bot is running"
    echo "  next      - ⏰ Show NEXT scheduled run times"
    echo "  dashboard - Show full monitoring dashboard"
    echo "  live      - Live auto-refresh dashboard"
    echo "  web       - Start web dashboard (browser)"
    echo "  logs      - Show recent message logs"
    echo "  watch     - Watch logs in real-time"
    echo "  start     - Start the automation"
    echo "  stop      - Stop the automation"
    echo "  restart   - Restart the automation"
    echo "  send      - Send messages now (manual)"
    echo "  grow      - Find & join groups now (manual)"
    echo "  groups    - List all target groups"
    echo "  config    - Open config file"
    echo "  help      - Show this help"
    echo ""
}

case "$1" in
    status)
        echo ""
        echo "🔍 Checking bot status..."
        echo ""
        result=$(launchctl list 2>/dev/null | grep techyera)
        if [ -n "$result" ]; then
            echo "✅ BOT IS RUNNING!"
            echo ""
            echo "$result"
            echo ""
            echo "Last activity:"
            tail -3 cron_messages.log 2>/dev/null | grep -E "(Sent|Completed|Started)" || echo "  No recent activity"
        else
            echo "❌ BOT IS NOT RUNNING"
            echo ""
            echo "To start: ./techyera.sh start"
        fi
        echo ""
        ;;
    
    dashboard)
        $PYTHON monitor.py
        ;;
    
    live)
        $PYTHON monitor.py --live
        ;;
    
    web)
        echo "🌐 Starting web dashboard..."
        echo "Open http://localhost:8080 in your browser"
        $PYTHON web_dashboard.py
        ;;
    
    logs)
        echo ""
        echo "📜 Recent Message Logs:"
        echo "════════════════════════════════════════════════════════"
        tail -20 cron_messages.log 2>/dev/null || echo "No logs yet"
        echo ""
        ;;
    
    watch)
        echo "👀 Watching logs in real-time (Ctrl+C to stop)..."
        echo ""
        tail -f cron_messages.log
        ;;
    
    start)
        echo "▶️ Starting automation..."
        bash install_launchd.sh
        ;;
    
    stop)
        echo "⏹️ Stopping automation..."
        bash uninstall_launchd.sh
        ;;
    
    restart)
        echo "🔄 Restarting automation..."
        bash uninstall_launchd.sh
        sleep 2
        bash install_launchd.sh
        ;;
    
    send)
        echo "📤 Sending messages now..."
        $PYTHON cron_send_messages.py
        ;;
    
    grow)
        echo "🌱 Finding & joining groups now..."
        $PYTHON cron_growth.py
        ;;
    
    groups)
        echo ""
        echo "🎯 Target Groups:"
        echo "════════════════════════════════════════════════════════"
        $PYTHON -c "
import json
c = json.load(open('config.json'))
print(f'Total: {len(c[\"targets\"])} groups\n')
for i, t in enumerate(c['targets'], 1):
    status = '✅' if t.get('enabled', True) else '❌'
    print(f'{i:2}. {status} {t[\"name\"][:40]:<40} {t.get(\"username\", \"\")}')
"
        echo ""
        ;;
    
    config)
        echo "📝 Opening config file..."
        open config.json
        ;;
    
    today)
        $PYTHON monitor.py --today
        ;;
    
    stats)
        $PYTHON monitor.py --stats
        ;;
    
    next)
        $PYTHON next_run.py
        ;;
    
    help|--help|-h|"")
        show_help
        ;;
    
    *)
        echo "Unknown command: $1"
        show_help
        ;;
esac
