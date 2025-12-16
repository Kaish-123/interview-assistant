#!/usr/bin/env python3
"""
📊 TECHYERA MARKETING MONITOR
==============================
Real-time monitoring dashboard for your Telegram marketing automation.
Shows all stats, logs, and activities.

Usage:
  python monitor.py           # Full dashboard
  python monitor.py --live    # Live updating dashboard
  python monitor.py --stats   # Quick stats only
  python monitor.py --today   # Today's activity only
"""

import json
import re
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Try to import colorama, fall back to no colors
try:
    from colorama import init, Fore, Style, Back
    init()
except ImportError:
    class Fore:
        GREEN = YELLOW = RED = CYAN = MAGENTA = BLUE = WHITE = ""
        RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""
    class Back:
        BLUE = ""

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
STATS_FILE = SCRIPT_DIR / "marketing_stats.json"

# Log files
LOG_FILES = {
    'messages': SCRIPT_DIR / "cron_messages.log",
    'growth': SCRIPT_DIR / "cron_growth.log",
    'master': SCRIPT_DIR / "master_automation.log",
    'master_output': SCRIPT_DIR / "master_automation_output.log",
}


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "total_messages_sent": 0,
        "total_groups_joined": 0,
        "daily_stats": {},
        "group_stats": {},
        "hourly_activity": {}
    }


def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)


def parse_log_file(log_path, max_lines=500):
    """Parse a log file and extract relevant information."""
    if not log_path.exists():
        return []
    
    entries = []
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()[-max_lines:]
            
        for line in lines:
            entry = parse_log_line(line)
            if entry:
                entries.append(entry)
    except Exception as e:
        pass
    
    return entries


def parse_log_line(line):
    """Parse a single log line."""
    # Pattern: 2025-12-11 02:28:08,986 - INFO - ✓ Sent to: ETL testing Support
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (\w+) - (.+)'
    match = re.match(pattern, line)
    
    if match:
        timestamp_str, level, message = match.groups()
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except:
            timestamp = None
        
        return {
            'timestamp': timestamp,
            'level': level,
            'message': message.strip(),
            'raw': line
        }
    return None


def analyze_logs():
    """Analyze all logs and extract statistics."""
    stats = {
        'messages_sent': [],
        'messages_failed': [],
        'groups_joined': [],
        'errors': [],
        'by_date': defaultdict(lambda: {'sent': 0, 'failed': 0, 'joined': 0}),
        'by_group': defaultdict(lambda: {'sent': 0, 'failed': 0, 'last_sent': None}),
    }
    
    # Parse message logs
    for log_name in ['messages', 'master', 'master_output']:
        log_path = LOG_FILES.get(log_name)
        if log_path and log_path.exists():
            entries = parse_log_file(log_path, max_lines=1000)
            
            for entry in entries:
                if not entry or not entry['timestamp']:
                    continue
                
                msg = entry['message']
                date_str = entry['timestamp'].strftime('%Y-%m-%d')
                
                # Sent messages
                if '✓ Sent to:' in msg or 'Sent to:' in msg:
                    group_match = re.search(r'Sent to[:\s]+(.+)', msg)
                    if group_match:
                        group_name = group_match.group(1).strip()
                        stats['messages_sent'].append({
                            'time': entry['timestamp'],
                            'group': group_name
                        })
                        stats['by_date'][date_str]['sent'] += 1
                        stats['by_group'][group_name]['sent'] += 1
                        stats['by_group'][group_name]['last_sent'] = entry['timestamp']
                
                # Failed messages
                elif 'No permission' in msg or 'Error' in msg or 'Failed' in msg:
                    stats['messages_failed'].append({
                        'time': entry['timestamp'],
                        'message': msg
                    })
                    stats['by_date'][date_str]['failed'] += 1
                
                # Joined groups
                elif '✓ Joined' in msg or 'Joined!' in msg:
                    group_match = re.search(r'Joined[:\s!]+(.+)', msg)
                    if group_match:
                        group_name = group_match.group(1).strip()
                        stats['groups_joined'].append({
                            'time': entry['timestamp'],
                            'group': group_name
                        })
                        stats['by_date'][date_str]['joined'] += 1
    
    return stats


def get_running_status():
    """Check if the automation is currently running."""
    import subprocess
    try:
        result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
        output = result.stdout
        
        send_running = 'com.techyera.telegram.send' in output
        growth_running = 'com.techyera.telegram.growth' in output
        
        return {
            'send': send_running,
            'growth': growth_running,
            'any': send_running or growth_running
        }
    except:
        return {'send': False, 'growth': False, 'any': False}


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print(f"""
{Fore.CYAN}{Style.BRIGHT}╔══════════════════════════════════════════════════════════════════╗
║           📊 TECHYERA TELEGRAM MARKETING MONITOR 📊               ║
║                    Real-time Dashboard                             ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)


def print_status_section(running_status):
    print(f"{Fore.YELLOW}{Style.BRIGHT}🔄 AUTOMATION STATUS{Style.RESET_ALL}")
    print("─" * 60)
    
    send_status = f"{Fore.GREEN}🟢 RUNNING{Style.RESET_ALL}" if running_status['send'] else f"{Fore.RED}🔴 STOPPED{Style.RESET_ALL}"
    growth_status = f"{Fore.GREEN}🟢 RUNNING{Style.RESET_ALL}" if running_status['growth'] else f"{Fore.RED}🔴 STOPPED{Style.RESET_ALL}"
    
    print(f"  Message Sender (hourly):  {send_status}")
    print(f"  Growth Engine (6-hourly): {growth_status}")
    print()


def print_stats_section(stats, config):
    print(f"{Fore.YELLOW}{Style.BRIGHT}📈 OVERALL STATISTICS{Style.RESET_ALL}")
    print("─" * 60)
    
    total_sent = len(stats['messages_sent'])
    total_failed = len(stats['messages_failed'])
    total_joined = len(stats['groups_joined'])
    total_groups = len(config.get('targets', []))
    
    print(f"  📤 Total Messages Sent:    {Fore.GREEN}{total_sent}{Style.RESET_ALL}")
    print(f"  ❌ Total Failed:           {Fore.RED}{total_failed}{Style.RESET_ALL}")
    print(f"  👥 Groups Joined:          {Fore.CYAN}{total_joined}{Style.RESET_ALL}")
    print(f"  🎯 Total Target Groups:    {Fore.MAGENTA}{total_groups}{Style.RESET_ALL}")
    
    if total_sent > 0:
        success_rate = (total_sent / (total_sent + total_failed)) * 100
        print(f"  ✅ Success Rate:           {Fore.GREEN}{success_rate:.1f}%{Style.RESET_ALL}")
    print()


def print_today_section(stats):
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = stats['by_date'].get(today, {'sent': 0, 'failed': 0, 'joined': 0})
    
    print(f"{Fore.YELLOW}{Style.BRIGHT}📅 TODAY'S ACTIVITY ({today}){Style.RESET_ALL}")
    print("─" * 60)
    print(f"  📤 Messages Sent:   {Fore.GREEN}{today_stats['sent']}{Style.RESET_ALL}")
    print(f"  ❌ Failed:          {Fore.RED}{today_stats['failed']}{Style.RESET_ALL}")
    print(f"  👥 Groups Joined:   {Fore.CYAN}{today_stats['joined']}{Style.RESET_ALL}")
    print()


def print_recent_messages(stats, limit=10):
    print(f"{Fore.YELLOW}{Style.BRIGHT}📤 RECENT MESSAGES SENT{Style.RESET_ALL}")
    print("─" * 60)
    
    recent = sorted(stats['messages_sent'], key=lambda x: x['time'], reverse=True)[:limit]
    
    if not recent:
        print(f"  {Fore.YELLOW}No messages sent yet{Style.RESET_ALL}")
    else:
        for msg in recent:
            time_str = msg['time'].strftime('%m/%d %H:%M')
            group = msg['group'][:40]
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} [{time_str}] {group}")
    print()


def print_recent_joins(stats, limit=10):
    print(f"{Fore.YELLOW}{Style.BRIGHT}👥 RECENTLY JOINED GROUPS{Style.RESET_ALL}")
    print("─" * 60)
    
    recent = sorted(stats['groups_joined'], key=lambda x: x['time'], reverse=True)[:limit]
    
    if not recent:
        print(f"  {Fore.YELLOW}No groups joined yet{Style.RESET_ALL}")
    else:
        for join in recent:
            time_str = join['time'].strftime('%m/%d %H:%M')
            group = join['group'][:40]
            print(f"  {Fore.CYAN}+{Style.RESET_ALL} [{time_str}] {group}")
    print()


def print_recent_errors(stats, limit=5):
    print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ RECENT ISSUES{Style.RESET_ALL}")
    print("─" * 60)
    
    recent = sorted(stats['messages_failed'], key=lambda x: x['time'], reverse=True)[:limit]
    
    if not recent:
        print(f"  {Fore.GREEN}No issues! Everything working fine.{Style.RESET_ALL}")
    else:
        for err in recent:
            time_str = err['time'].strftime('%m/%d %H:%M')
            msg = err['message'][:50]
            print(f"  {Fore.RED}✗{Style.RESET_ALL} [{time_str}] {msg}")
    print()


def print_group_stats(stats, limit=15):
    print(f"{Fore.YELLOW}{Style.BRIGHT}📊 TOP GROUPS BY MESSAGES{Style.RESET_ALL}")
    print("─" * 60)
    
    sorted_groups = sorted(
        stats['by_group'].items(),
        key=lambda x: x[1]['sent'],
        reverse=True
    )[:limit]
    
    if not sorted_groups:
        print(f"  {Fore.YELLOW}No group stats yet{Style.RESET_ALL}")
    else:
        print(f"  {'Group':<40} {'Sent':>6} {'Last Sent':>12}")
        print(f"  {'-'*40} {'-'*6} {'-'*12}")
        for group, data in sorted_groups:
            last_sent = data['last_sent'].strftime('%m/%d %H:%M') if data['last_sent'] else 'Never'
            group_display = group[:38] + '..' if len(group) > 40 else group
            print(f"  {group_display:<40} {Fore.GREEN}{data['sent']:>6}{Style.RESET_ALL} {last_sent:>12}")
    print()


def print_daily_history(stats, days=7):
    print(f"{Fore.YELLOW}{Style.BRIGHT}📅 DAILY HISTORY (Last {days} days){Style.RESET_ALL}")
    print("─" * 60)
    
    print(f"  {'Date':<12} {'Sent':>8} {'Failed':>8} {'Joined':>8}")
    print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8}")
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_stats = stats['by_date'].get(date, {'sent': 0, 'failed': 0, 'joined': 0})
        
        sent_color = Fore.GREEN if day_stats['sent'] > 0 else Fore.WHITE
        failed_color = Fore.RED if day_stats['failed'] > 0 else Fore.WHITE
        joined_color = Fore.CYAN if day_stats['joined'] > 0 else Fore.WHITE
        
        print(f"  {date:<12} {sent_color}{day_stats['sent']:>8}{Style.RESET_ALL} {failed_color}{day_stats['failed']:>8}{Style.RESET_ALL} {joined_color}{day_stats['joined']:>8}{Style.RESET_ALL}")
    print()


def print_next_runs():
    print(f"{Fore.YELLOW}{Style.BRIGHT}⏰ SCHEDULE{Style.RESET_ALL}")
    print("─" * 60)
    
    now = datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    next_6h = now.replace(minute=0, second=0, microsecond=0)
    while next_6h.hour % 6 != 0:
        next_6h += timedelta(hours=1)
    if next_6h <= now:
        next_6h += timedelta(hours=6)
    
    time_to_msg = next_hour - now
    time_to_growth = next_6h - now
    
    print(f"  📤 Next message batch:  {next_hour.strftime('%H:%M')} (in {int(time_to_msg.seconds/60)} min)")
    print(f"  🌱 Next growth cycle:   {next_6h.strftime('%H:%M')} (in {int(time_to_growth.seconds/60)} min)")
    print()


def print_help():
    print(f"{Fore.YELLOW}{Style.BRIGHT}💡 COMMANDS{Style.RESET_ALL}")
    print("─" * 60)
    print(f"  {Fore.CYAN}tail -f cron_messages.log{Style.RESET_ALL}  - Live message log")
    print(f"  {Fore.CYAN}tail -f cron_growth.log{Style.RESET_ALL}    - Live growth log")
    print(f"  {Fore.CYAN}python monitor.py --live{Style.RESET_ALL}   - Auto-refresh dashboard")
    print(f"  {Fore.CYAN}launchctl list | grep techyera{Style.RESET_ALL} - Check status")
    print()


def show_full_dashboard():
    """Show the complete dashboard."""
    clear_screen()
    print_header()
    
    config = load_config()
    stats = analyze_logs()
    running = get_running_status()
    
    print_status_section(running)
    print_stats_section(stats, config)
    print_today_section(stats)
    print_next_runs()
    print_recent_messages(stats, limit=8)
    print_recent_joins(stats, limit=5)
    print_recent_errors(stats, limit=3)
    print_group_stats(stats, limit=10)
    print_daily_history(stats, days=7)
    print_help()
    
    print(f"{Fore.CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")


def show_live_dashboard():
    """Show auto-updating dashboard."""
    try:
        while True:
            show_full_dashboard()
            print(f"\n{Fore.YELLOW}Auto-refreshing every 30 seconds... Press Ctrl+C to exit{Style.RESET_ALL}")
            time.sleep(30)
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}Dashboard closed.{Style.RESET_ALL}")


def show_quick_stats():
    """Show quick stats only."""
    config = load_config()
    stats = analyze_logs()
    running = get_running_status()
    
    print(f"\n{Fore.CYAN}📊 Quick Stats:{Style.RESET_ALL}")
    print(f"  Status: {'🟢 Running' if running['any'] else '🔴 Stopped'}")
    print(f"  Messages Sent: {len(stats['messages_sent'])}")
    print(f"  Groups Joined: {len(stats['groups_joined'])}")
    print(f"  Total Targets: {len(config.get('targets', []))}")
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = stats['by_date'].get(today, {'sent': 0})
    print(f"  Today's Messages: {today_stats['sent']}")


def show_today_only():
    """Show today's activity only."""
    stats = analyze_logs()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{Fore.CYAN}📅 Today's Activity ({today}):{Style.RESET_ALL}")
    print("─" * 50)
    
    # Today's messages
    today_msgs = [m for m in stats['messages_sent'] 
                  if m['time'].strftime('%Y-%m-%d') == today]
    
    print(f"\n{Fore.GREEN}Messages Sent ({len(today_msgs)}):{Style.RESET_ALL}")
    for msg in sorted(today_msgs, key=lambda x: x['time']):
        print(f"  [{msg['time'].strftime('%H:%M')}] {msg['group'][:50]}")
    
    # Today's joins
    today_joins = [j for j in stats['groups_joined'] 
                   if j['time'].strftime('%Y-%m-%d') == today]
    
    print(f"\n{Fore.CYAN}Groups Joined ({len(today_joins)}):{Style.RESET_ALL}")
    for join in sorted(today_joins, key=lambda x: x['time']):
        print(f"  [{join['time'].strftime('%H:%M')}] {join['group'][:50]}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == '--live':
            show_live_dashboard()
        elif arg == '--stats':
            show_quick_stats()
        elif arg == '--today':
            show_today_only()
        elif arg == '--help':
            print("Usage: python monitor.py [--live|--stats|--today]")
        else:
            show_full_dashboard()
    else:
        show_full_dashboard()

