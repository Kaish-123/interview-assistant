#!/bin/bash
# Setup Cron Jobs for Telegram Marketing Automation
# This script sets up cron jobs for fully automated marketing

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
LOG_DIR="$SCRIPT_DIR"

echo "🔧 Setting up Cron Jobs for TechyEra Marketing..."
echo ""

# Create the cron entries
CRON_SEND="0 * * * * cd $SCRIPT_DIR && $PYTHON_PATH cron_send_messages.py >> $LOG_DIR/cron_send.log 2>&1"
CRON_GROWTH="0 */6 * * * cd $SCRIPT_DIR && $PYTHON_PATH cron_growth.py >> $LOG_DIR/cron_growth_run.log 2>&1"

# Backup existing crontab
crontab -l > /tmp/current_cron 2>/dev/null || echo "" > /tmp/current_cron

# Remove any existing telegram marketing entries
grep -v "cron_send_messages.py\|cron_growth.py" /tmp/current_cron > /tmp/new_cron

# Add new entries
echo "" >> /tmp/new_cron
echo "# TechyEra Telegram Marketing Automation" >> /tmp/new_cron
echo "$CRON_SEND" >> /tmp/new_cron
echo "$CRON_GROWTH" >> /tmp/new_cron

# Install new crontab
crontab /tmp/new_cron

echo "✅ Cron jobs installed!"
echo ""
echo "📋 Scheduled Tasks:"
echo "   • Send Messages: Every hour (at minute 0)"
echo "   • Growth (find/join): Every 6 hours"
echo ""
echo "📂 Log files:"
echo "   • $LOG_DIR/cron_messages.log"
echo "   • $LOG_DIR/cron_growth.log"
echo ""
echo "🔍 View current cron jobs: crontab -l"
echo "❌ Remove cron jobs: crontab -r"
echo ""

# Show current crontab
echo "Current crontab:"
echo "----------------"
crontab -l | grep -E "(telegram|cron_send|cron_growth|TechyEra)"

