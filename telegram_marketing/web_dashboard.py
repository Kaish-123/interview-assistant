#!/usr/bin/env python3
"""
🌐 TECHYERA WEB DASHBOARD
==========================
A simple web-based dashboard to monitor your Telegram marketing.
Open http://localhost:8080 in your browser.

Usage:
  python web_dashboard.py
"""

import json
import re
import http.server
import socketserver
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
PORT = 8080

LOG_FILES = {
    'messages': SCRIPT_DIR / "cron_messages.log",
    'growth': SCRIPT_DIR / "cron_growth.log",
}


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def parse_logs():
    """Parse logs and return stats."""
    stats = {
        'messages_sent': [],
        'messages_failed': [],
        'groups_joined': [],
        'by_date': defaultdict(lambda: {'sent': 0, 'failed': 0, 'joined': 0}),
        'by_group': defaultdict(lambda: {'sent': 0, 'last_sent': None}),
    }
    
    for log_path in LOG_FILES.values():
        if not log_path.exists():
            continue
        
        try:
            with open(log_path, 'r') as f:
                for line in f.readlines()[-500:]:
                    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (\w+) - (.+)'
                    match = re.match(pattern, line)
                    
                    if match:
                        timestamp_str, level, message = match.groups()
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            continue
                        
                        date_str = timestamp.strftime('%Y-%m-%d')
                        
                        if '✓ Sent to:' in message:
                            group_match = re.search(r'Sent to[:\s]+(.+)', message)
                            if group_match:
                                group = group_match.group(1).strip()
                                stats['messages_sent'].append({
                                    'time': timestamp.isoformat(),
                                    'group': group
                                })
                                stats['by_date'][date_str]['sent'] += 1
                                stats['by_group'][group]['sent'] += 1
                                stats['by_group'][group]['last_sent'] = timestamp.isoformat()
                        
                        elif 'No permission' in message or 'Error' in message:
                            stats['messages_failed'].append({
                                'time': timestamp.isoformat(),
                                'message': message[:100]
                            })
                            stats['by_date'][date_str]['failed'] += 1
                        
                        elif '✓ Joined' in message or 'Joined!' in message:
                            group_match = re.search(r'Joined[:\s!]+(.+)', message)
                            if group_match:
                                group = group_match.group(1).strip()
                                stats['groups_joined'].append({
                                    'time': timestamp.isoformat(),
                                    'group': group
                                })
                                stats['by_date'][date_str]['joined'] += 1
        except Exception as e:
            pass
    
    return stats


def generate_html():
    """Generate HTML dashboard."""
    config = load_config()
    stats = parse_logs()
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_stats = stats['by_date'].get(today, {'sent': 0, 'failed': 0, 'joined': 0})
    
    total_sent = len(stats['messages_sent'])
    total_failed = len(stats['messages_failed'])
    total_joined = len(stats['groups_joined'])
    total_groups = len(config.get('targets', []))
    
    # Recent messages HTML
    recent_msgs = sorted(stats['messages_sent'], key=lambda x: x['time'], reverse=True)[:20]
    msgs_html = ""
    for msg in recent_msgs:
        time_str = msg['time'][11:16]  # HH:MM
        date_str = msg['time'][:10]
        msgs_html += f'<tr><td>{date_str}</td><td>{time_str}</td><td>{msg["group"][:50]}</td></tr>'
    
    # Recent joins HTML
    recent_joins = sorted(stats['groups_joined'], key=lambda x: x['time'], reverse=True)[:10]
    joins_html = ""
    for join in recent_joins:
        time_str = join['time'][11:16]
        date_str = join['time'][:10]
        joins_html += f'<tr><td>{date_str}</td><td>{time_str}</td><td>{join["group"][:50]}</td></tr>'
    
    # Daily stats HTML
    daily_html = ""
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day = stats['by_date'].get(date, {'sent': 0, 'failed': 0, 'joined': 0})
        daily_html += f'<tr><td>{date}</td><td>{day["sent"]}</td><td>{day["failed"]}</td><td>{day["joined"]}</td></tr>'
    
    # Groups list HTML
    groups_html = ""
    for target in config.get('targets', [])[:30]:
        status = "✅" if target.get('enabled', True) else "❌"
        groups_html += f'<tr><td>{status}</td><td>{target.get("name", "")[:40]}</td><td>{target.get("username", "")}</td></tr>'
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>TechyEra Marketing Dashboard</title>
    <meta http-equiv="refresh" content="60">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ 
            text-align: center; 
            padding: 20px; 
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5em;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-card h3 {{ color: #888; font-size: 0.9em; margin-bottom: 10px; }}
        .stat-card .number {{ font-size: 2.5em; font-weight: bold; }}
        .stat-card.green .number {{ color: #00ff88; }}
        .stat-card.red .number {{ color: #ff4757; }}
        .stat-card.blue .number {{ color: #00d4ff; }}
        .stat-card.purple .number {{ color: #a855f7; }}
        .stat-card.yellow .number {{ color: #ffd93d; }}
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #888; font-weight: 500; }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .status {{ 
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        .status.running {{ background: #00ff8833; color: #00ff88; }}
        .status.stopped {{ background: #ff475733; color: #ff4757; }}
        .updated {{ text-align: center; color: #666; margin-top: 20px; font-size: 0.9em; }}
        @media (max-width: 768px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 TechyEra Marketing Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card green">
                <h3>📤 TOTAL MESSAGES SENT</h3>
                <div class="number">{total_sent}</div>
            </div>
            <div class="stat-card blue">
                <h3>👥 GROUPS JOINED</h3>
                <div class="number">{total_joined}</div>
            </div>
            <div class="stat-card purple">
                <h3>🎯 TARGET GROUPS</h3>
                <div class="number">{total_groups}</div>
            </div>
            <div class="stat-card yellow">
                <h3>📅 TODAY'S MESSAGES</h3>
                <div class="number">{today_stats['sent']}</div>
            </div>
            <div class="stat-card red">
                <h3>❌ TODAY'S FAILED</h3>
                <div class="number">{today_stats['failed']}</div>
            </div>
        </div>
        
        <div class="grid-2">
            <div class="section">
                <h2>📤 Recent Messages Sent</h2>
                <table>
                    <tr><th>Date</th><th>Time</th><th>Group</th></tr>
                    {msgs_html}
                </table>
            </div>
            
            <div class="section">
                <h2>👥 Recently Joined Groups</h2>
                <table>
                    <tr><th>Date</th><th>Time</th><th>Group</th></tr>
                    {joins_html}
                </table>
            </div>
        </div>
        
        <div class="grid-2">
            <div class="section">
                <h2>📅 Daily Statistics (Last 7 Days)</h2>
                <table>
                    <tr><th>Date</th><th>Sent</th><th>Failed</th><th>Joined</th></tr>
                    {daily_html}
                </table>
            </div>
            
            <div class="section">
                <h2>🎯 Target Groups</h2>
                <table>
                    <tr><th>Status</th><th>Name</th><th>Username</th></tr>
                    {groups_html}
                </table>
            </div>
        </div>
        
        <p class="updated">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refreshes every 60 seconds</p>
    </div>
</body>
</html>
'''
    return html


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(generate_html().encode())
        elif self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            stats = parse_logs()
            self.wfile.write(json.dumps(stats, default=str).encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║       🌐 TECHYERA WEB DASHBOARD                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   Dashboard running at: http://localhost:{PORT}           ║
║                                                          ║
║   Open this URL in your browser!                         ║
║                                                          ║
║   Press Ctrl+C to stop                                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard stopped.")


if __name__ == "__main__":
    main()

