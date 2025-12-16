#!/usr/bin/env python3
"""
Easy WhatsApp Marketing - Simple CLI Tool
==========================================
FREE WhatsApp automation using GUI (no API costs!)
Just add phone numbers to contacts.txt and run!

Author: TechyEra Marketing Suite
"""

import subprocess
import time
import sys
import json
import os
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import pyautogui
except ImportError:
    print("❌ Installing pyautogui...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui"])
    import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# Paths
SCRIPT_DIR = Path(__file__).parent
CONTACTS_FILE = SCRIPT_DIR / "contacts.txt"
MESSAGES_FILE = SCRIPT_DIR / "messages.txt"
CONFIG_FILE = SCRIPT_DIR / "easy_config.json"
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def log(msg: str, level: str = "INFO"):
    """Log with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] [{level}] {msg}"
    print(formatted)
    
    log_file = LOG_DIR / f"easy_{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, 'a') as f:
        f.write(formatted + "\n")


def load_config() -> dict:
    """Load configuration."""
    default = {
        "delay_min_seconds": 30,
        "delay_max_seconds": 60,
        "schedule_interval_minutes": 60,
        "active_hours": {"start": 9, "end": 21},
        "max_per_run": 50
    }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            for k, v in default.items():
                if k not in config:
                    config[k] = v
            return config
    except FileNotFoundError:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default, f, indent=4)
        return default


def load_contacts() -> list:
    """Load phone numbers from contacts.txt"""
    if not CONTACTS_FILE.exists():
        # Create sample file
        sample = """# WhatsApp Marketing Contacts
# Add one phone number per line (with country code)
# Lines starting with # are ignored
# Format: PHONE,NAME (name is optional)

# Example:
# 919876543210,John Client
# 919876543211,Jane Proxy
"""
        with open(CONTACTS_FILE, 'w') as f:
            f.write(sample)
        log(f"📝 Created {CONTACTS_FILE} - Add your contacts there!")
        return []
    
    contacts = []
    with open(CONTACTS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(',', 1)
                phone = parts[0].strip().replace('+', '').replace(' ', '').replace('-', '')
                name = parts[1].strip() if len(parts) > 1 else phone
                if phone:
                    contacts.append({"phone": phone, "name": name})
    
    return contacts


def load_messages() -> list:
    """Load messages from messages.txt"""
    if not MESSAGES_FILE.exists():
        # Create sample file
        sample = """# WhatsApp Marketing Messages
# Separate each message with a line containing only: ---
# Messages will be rotated

Hello! 👋

Please refer me to your known friends and consultancies for:
📊 Data Engineering
📈 Data Analyst  
💻 Amazon SDE Interview Proxy
📝 Technical Assessments

Your referral is highly appreciated!

Thanks!
---
🎯 Special Opportunity!

Looking for data engineering and analytics roles.
Can help with interview preparation and proxy interviews.

Reply if interested!
---
Hi there! 

Quick update - I'm available for:
✅ Data Engineering projects
✅ Interview assistance
✅ Technical assessments

Let me know if you have any leads!
"""
        with open(MESSAGES_FILE, 'w') as f:
            f.write(sample)
        log(f"📝 Created {MESSAGES_FILE} - Edit your messages there!")
    
    with open(MESSAGES_FILE, 'r') as f:
        content = f.read()
    
    # Split by separator, remove comment lines
    messages = []
    for msg in content.split('---'):
        lines = [l for l in msg.strip().split('\n') if not l.strip().startswith('#')]
        cleaned = '\n'.join(lines).strip()
        if cleaned:
            messages.append(cleaned)
    
    return messages if messages else ["Hello! This is a test message."]


def copy_to_clipboard(text: str):
    """Copy text to clipboard."""
    p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    p.communicate(text.encode('utf-8'))
    p.wait()
    time.sleep(0.2)


def open_whatsapp():
    """Open and activate WhatsApp Desktop."""
    log("📱 Opening WhatsApp Desktop...")
    
    subprocess.run(["open", "-a", "WhatsApp"], check=True)
    time.sleep(2)
    
    # Activate and focus
    script = '''
    tell application "WhatsApp"
        activate
    end tell
    delay 1
    tell application "System Events"
        tell process "WhatsApp"
            set frontmost to true
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True)
    time.sleep(2)
    
    # Click to focus
    pyautogui.click(700, 400)
    time.sleep(0.5)
    log("   ✅ WhatsApp ready")


def send_message_to_phone(phone: str, name: str, message: str) -> bool:
    """Send message to a phone number."""
    log(f"📤 Sending to: {name} ({phone})")
    
    try:
        # Close any dialogs
        pyautogui.press('escape')
        time.sleep(0.3)
        pyautogui.press('escape')
        time.sleep(0.5)
        
        # Open new chat (Cmd+N)
        pyautogui.hotkey('command', 'n')
        time.sleep(1.5)
        
        # Select all and paste phone
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)
        
        # Format phone with country code if needed
        if not phone.startswith('+'):
            if len(phone) == 10:
                phone = '+91' + phone
            else:
                phone = '+' + phone
        
        copy_to_clipboard(phone)
        pyautogui.hotkey('command', 'v')
        time.sleep(2)
        
        # Select first result and open chat
        pyautogui.press('down')
        time.sleep(0.3)
        pyautogui.press('return')
        time.sleep(1.5)
        
        # Click message input area
        pyautogui.click(700, 820)
        time.sleep(0.5)
        
        # Clear and paste message
        pyautogui.hotkey('command', 'a')
        time.sleep(0.1)
        copy_to_clipboard(message)
        pyautogui.hotkey('command', 'v')
        time.sleep(0.5)
        
        # Send
        pyautogui.press('return')
        time.sleep(1)
        
        log(f"   ✅ Sent to {name}")
        return True
        
    except Exception as e:
        log(f"   ❌ Error: {e}", "ERROR")
        return False


def run_campaign(limit: int = None, dry_run: bool = False):
    """Run marketing campaign."""
    log("\n" + "=" * 60)
    log("🚀 WHATSAPP MARKETING CAMPAIGN")
    log("=" * 60)
    
    config = load_config()
    contacts = load_contacts()
    messages = load_messages()
    
    if not contacts:
        log(f"❌ No contacts! Add phone numbers to: {CONTACTS_FILE}")
        return
    
    if limit:
        contacts = contacts[:limit]
    
    max_per_run = config.get('max_per_run', 50)
    contacts = contacts[:max_per_run]
    
    log(f"📋 Contacts: {len(contacts)}")
    log(f"💬 Messages: {len(messages)} (will rotate)")
    log(f"🧪 Dry Run: {dry_run}")
    log("")
    
    if dry_run:
        for i, c in enumerate(contacts):
            msg = messages[i % len(messages)]
            log(f"[DRY] Would send to {c['name']} ({c['phone']})")
            log(f"      Message: {msg[:50]}...")
        return {"success": len(contacts), "failed": 0}
    
    # Open WhatsApp
    open_whatsapp()
    time.sleep(2)
    
    delay_min = config.get('delay_min_seconds', 30)
    delay_max = config.get('delay_max_seconds', 60)
    
    results = {"success": 0, "failed": 0}
    
    for i, contact in enumerate(contacts):
        message = messages[i % len(messages)]
        
        log(f"\n[{i+1}/{len(contacts)}]")
        success = send_message_to_phone(contact['phone'], contact['name'], message)
        
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
        
        # Delay between messages
        if i < len(contacts) - 1:
            delay = random.randint(delay_min, delay_max)
            log(f"⏳ Waiting {delay}s...")
            time.sleep(delay)
    
    log("\n" + "=" * 60)
    log("📊 RESULTS")
    log(f"   ✅ Success: {results['success']}")
    log(f"   ❌ Failed: {results['failed']}")
    log("=" * 60)
    
    return results


def run_scheduler():
    """Run continuous scheduler."""
    config = load_config()
    interval = config.get('schedule_interval_minutes', 60)
    active_hours = config.get('active_hours', {'start': 9, 'end': 21})
    
    log("\n🔄 SCHEDULER STARTED")
    log(f"   Interval: Every {interval} minutes")
    log(f"   Active hours: {active_hours['start']}:00 - {active_hours['end']}:00")
    log("   Press Ctrl+C to stop\n")
    
    while True:
        try:
            now = datetime.now()
            
            # Check active hours
            if active_hours['start'] <= now.hour < active_hours['end']:
                run_campaign()
            else:
                log(f"⏰ Outside active hours ({active_hours['start']}-{active_hours['end']}). Skipping...")
            
            # Calculate next run
            next_run = now + timedelta(minutes=interval)
            log(f"\n⏰ Next run: {next_run.strftime('%H:%M:%S')}")
            
            time.sleep(interval * 60)
            
        except KeyboardInterrupt:
            log("\n👋 Scheduler stopped")
            break


def test_single(phone: str, message: str = None):
    """Test with single phone number."""
    log(f"\n🧪 TEST MODE: {phone}")
    
    messages = load_messages()
    msg = message or messages[0]
    
    open_whatsapp()
    time.sleep(2)
    
    success = send_message_to_phone(phone, "Test", msg)
    
    if success:
        log("\n✅ TEST SUCCESSFUL!")
    else:
        log("\n❌ TEST FAILED!")


def show_status():
    """Show current status."""
    print("\n📊 WHATSAPP MARKETING STATUS")
    print("=" * 50)
    
    contacts = load_contacts()
    messages = load_messages()
    config = load_config()
    
    print(f"\n📋 Contacts: {len(contacts)}")
    if contacts:
        print("   First 5:")
        for c in contacts[:5]:
            print(f"   • {c['name']} ({c['phone']})")
        if len(contacts) > 5:
            print(f"   ... and {len(contacts) - 5} more")
    
    print(f"\n💬 Messages: {len(messages)}")
    for i, m in enumerate(messages[:3]):
        print(f"   [{i+1}] {m[:40]}...")
    
    print(f"\n⚙️  Config:")
    print(f"   Delay: {config['delay_min_seconds']}-{config['delay_max_seconds']}s")
    print(f"   Max per run: {config.get('max_per_run', 50)}")
    print(f"   Schedule: Every {config.get('schedule_interval_minutes', 60)} min")
    print(f"   Active hours: {config['active_hours']['start']}-{config['active_hours']['end']}")
    
    print(f"\n📁 Files:")
    print(f"   Contacts: {CONTACTS_FILE}")
    print(f"   Messages: {MESSAGES_FILE}")
    print(f"   Config: {CONFIG_FILE}")
    print(f"   Logs: {LOG_DIR}/")


def add_contact(phone: str, name: str = None):
    """Add a contact to the list."""
    name = name or phone
    with open(CONTACTS_FILE, 'a') as f:
        f.write(f"\n{phone},{name}")
    print(f"✅ Added: {name} ({phone})")


def main():
    parser = argparse.ArgumentParser(
        description="Easy WhatsApp Marketing - FREE CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python easy_whatsapp.py --status           # Show status
  python easy_whatsapp.py --run              # Run campaign
  python easy_whatsapp.py --run --limit 5    # Send to first 5 only
  python easy_whatsapp.py --run --dry-run    # Test without sending
  python easy_whatsapp.py --test 919876543210  # Test single number
  python easy_whatsapp.py --schedule         # Run on schedule
  python easy_whatsapp.py --add 919876543210 "John"  # Add contact

Files:
  contacts.txt  - Add phone numbers here (one per line)
  messages.txt  - Add messages here (separated by ---)
        """
    )
    
    parser.add_argument('--status', '-s', action='store_true', help='Show status')
    parser.add_argument('--run', '-r', action='store_true', help='Run campaign now')
    parser.add_argument('--schedule', action='store_true', help='Run on schedule')
    parser.add_argument('--test', '-t', type=str, metavar='PHONE', help='Test with single phone')
    parser.add_argument('--add', '-a', nargs='+', metavar=('PHONE', 'NAME'), help='Add contact')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of contacts')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run (no actual sending)')
    parser.add_argument('--message', '-m', type=str, help='Custom message for test')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.run:
        run_campaign(limit=args.limit, dry_run=args.dry_run)
    elif args.schedule:
        run_scheduler()
    elif args.test:
        test_single(args.test, args.message)
    elif args.add:
        phone = args.add[0]
        name = args.add[1] if len(args.add) > 1 else None
        add_contact(phone, name)
    else:
        parser.print_help()
        print("\n" + "=" * 50)
        print("🚀 QUICK START:")
        print("=" * 50)
        print("1. Edit contacts.txt - Add phone numbers")
        print("2. Edit messages.txt - Add your messages")
        print("3. Run: python easy_whatsapp.py --run")
        print("")
        print("💡 This is FREE - No API costs!")
        print("⚠️  Keep WhatsApp Desktop open and screen on")


if __name__ == "__main__":
    main()

