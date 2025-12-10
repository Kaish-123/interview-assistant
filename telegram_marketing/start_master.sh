#!/bin/bash
# TechyEra Master Automation Starter
# This starts the fully automated marketing bot

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting TechyEra Master Automation..."
echo ""

# Kill any existing automation processes
pkill -f "telegram_marketer.py" 2>/dev/null
pkill -f "master_automation.py" 2>/dev/null
sleep 2

# Activate virtual environment
source venv/bin/activate

# Start master automation in background
nohup python master_automation.py > master_automation_output.log 2>&1 &

echo "✅ Master Automation started!"
echo ""
echo "📊 What it does:"
echo "   • Sends messages every 60 minutes"
echo "   • Finds new groups every 6 hours"
echo "   • Joins them automatically"
echo "   • Adds them to config"
echo "   • Runs 24/7"
echo ""
echo "📋 Useful commands:"
echo "   • View live log: tail -f master_automation.log"
echo "   • View output: tail -f master_automation_output.log"
echo "   • Stop bot: pkill -f master_automation.py"
echo ""
