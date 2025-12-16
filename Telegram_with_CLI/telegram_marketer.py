#!/usr/bin/env python3
"""
Telegram Marketing Automation Tool
===================================
Automated message sender for Telegram groups and channels.
Author: TechyEra Marketing Suite
"""

import json
import asyncio
import random
import logging
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from telethon import TelegramClient, errors
from telethon.tl.types import Channel, Chat, User
from colorama import init, Fore, Style

# Initialize colorama
init()

# Constants
CONFIG_FILE = "config.json"
SCRIPT_DIR = Path(__file__).parent


class TelegramMarketer:
    """Main class for Telegram marketing automation."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or SCRIPT_DIR / CONFIG_FILE
        self.config = self._load_config()
        self.client: Optional[TelegramClient] = None
        self.message_index = 0
        self.messages_sent_today = 0
        self.last_reset_date = datetime.now().date()
        self._setup_logging()
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}Config file not found: {self.config_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Run 'python telegram_marketer.py --setup' to create one.{Style.RESET_ALL}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Invalid JSON in config file: {e}{Style.RESET_ALL}")
            sys.exit(1)
    
    def _save_config(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def _setup_logging(self):
        """Configure logging."""
        log_file = self.config.get('settings', {}).get('log_file', 'telegram_marketing.log')
        log_path = SCRIPT_DIR / log_file
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _print_banner(self):
        """Print application banner."""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║           📱 TELEGRAM MARKETING AUTOMATION 📱              ║
║                    TechyEra Suite                          ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
    
    async def connect(self) -> bool:
        """Connect to Telegram API."""
        api_id = self.config.get('api_id')
        api_hash = self.config.get('api_hash')
        phone = self.config.get('phone_number')
        session_name = self.config.get('session_name', 'marketing_session')
        
        if not all([api_id, api_hash, phone]):
            print(f"{Fore.RED}Missing API credentials in config.json{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please fill in api_id, api_hash, and phone_number{Style.RESET_ALL}")
            return False
        
        session_path = SCRIPT_DIR / session_name
        self.client = TelegramClient(str(session_path), api_id, api_hash)
        
        try:
            await self.client.start(phone=phone)
            me = await self.client.get_me()
            print(f"{Fore.GREEN}✓ Connected as: {me.first_name} (@{me.username}){Style.RESET_ALL}")
            self.logger.info(f"Connected as {me.first_name} (@{me.username})")
            return True
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            self.logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            print(f"{Fore.YELLOW}Disconnected from Telegram{Style.RESET_ALL}")
    
    async def list_dialogs(self):
        """List all available groups and channels."""
        print(f"\n{Fore.CYAN}📋 Your Groups & Channels:{Style.RESET_ALL}")
        print("-" * 60)
        
        groups = []
        channels = []
        
        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            
            if isinstance(entity, Channel):
                if entity.megagroup:
                    groups.append({
                        'name': dialog.name,
                        'id': entity.id,
                        'username': f"@{entity.username}" if entity.username else f"ID:{entity.id}"
                    })
                else:
                    channels.append({
                        'name': dialog.name,
                        'id': entity.id,
                        'username': f"@{entity.username}" if entity.username else f"ID:{entity.id}"
                    })
            elif isinstance(entity, Chat):
                groups.append({
                    'name': dialog.name,
                    'id': entity.id,
                    'username': f"ID:{entity.id}"
                })
        
        print(f"\n{Fore.GREEN}📢 Channels ({len(channels)}):{Style.RESET_ALL}")
        for ch in channels[:20]:
            print(f"  • {ch['name']} [{ch['username']}]")
        
        print(f"\n{Fore.BLUE}👥 Groups ({len(groups)}):{Style.RESET_ALL}")
        for gr in groups[:30]:
            print(f"  • {gr['name']} [{gr['username']}]")
        
        print(f"\n{Fore.YELLOW}Tip: Copy the username/ID to add to your config.json targets{Style.RESET_ALL}")
        return groups, channels
    
    def _get_next_message(self) -> Optional[str]:
        """Get the next message to send (rotation support)."""
        enabled_messages = [m for m in self.config['messages'] if m.get('enabled', True)]
        
        if not enabled_messages:
            return None
        
        if self.config['settings'].get('rotate_messages', True):
            message = enabled_messages[self.message_index % len(enabled_messages)]
            self.message_index += 1
        else:
            message = random.choice(enabled_messages)
        
        return message['text']
    
    def _is_within_active_hours(self) -> bool:
        """Check if current time is within active hours."""
        schedule = self.config.get('schedule', {})
        if not schedule.get('enabled', True):
            return True
        
        now = datetime.now()
        active_hours = schedule.get('active_hours', {})
        start_hour = active_hours.get('start', 0)
        end_hour = active_hours.get('end', 24)
        
        active_days = schedule.get('active_days', [0, 1, 2, 3, 4, 5, 6])
        
        if now.weekday() not in active_days:
            return False
        
        return start_hour <= now.hour < end_hour
    
    def _check_daily_limit(self) -> bool:
        """Check if daily message limit is reached."""
        today = datetime.now().date()
        
        if today != self.last_reset_date:
            self.messages_sent_today = 0
            self.last_reset_date = today
        
        max_daily = self.config['settings'].get('max_messages_per_day', 50)
        return self.messages_sent_today < max_daily
    
    async def send_to_target(self, target: dict, message: str) -> bool:
        """Send message to a single target."""
        target_id = target.get('username') or target.get('id')
        
        try:
            # Handle both username and ID formats
            if isinstance(target_id, str) and target_id.startswith('@'):
                entity = await self.client.get_entity(target_id)
            elif isinstance(target_id, str) and target_id.startswith('ID:'):
                entity = await self.client.get_entity(int(target_id[3:]))
            else:
                entity = await self.client.get_entity(target_id)
            
            await self.client.send_message(entity, message)
            self.messages_sent_today += 1
            
            print(f"{Fore.GREEN}✓ Sent to: {target['name']}{Style.RESET_ALL}")
            self.logger.info(f"Message sent to {target['name']}")
            return True
            
        except errors.FloodWaitError as e:
            wait_time = e.seconds
            print(f"{Fore.RED}⚠ Flood wait: sleeping for {wait_time}s{Style.RESET_ALL}")
            self.logger.warning(f"Flood wait: {wait_time}s")
            await asyncio.sleep(wait_time)
            return False
            
        except errors.ChatWriteForbiddenError:
            print(f"{Fore.RED}✗ Cannot write to: {target['name']} (no permission){Style.RESET_ALL}")
            self.logger.warning(f"No write permission for {target['name']}")
            return False
            
        except errors.UserBannedInChannelError:
            print(f"{Fore.RED}✗ Banned in: {target['name']}{Style.RESET_ALL}")
            self.logger.warning(f"Banned from {target['name']}")
            return False
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error sending to {target['name']}: {e}{Style.RESET_ALL}")
            self.logger.error(f"Error sending to {target['name']}: {e}")
            return False
    
    async def send_to_all(self):
        """Send message to all enabled targets."""
        if not self._is_within_active_hours():
            print(f"{Fore.YELLOW}⏰ Outside active hours. Skipping...{Style.RESET_ALL}")
            return
        
        if not self._check_daily_limit():
            print(f"{Fore.YELLOW}📊 Daily limit reached. Waiting until tomorrow...{Style.RESET_ALL}")
            return
        
        message = self._get_next_message()
        if not message:
            print(f"{Fore.RED}No enabled messages in config{Style.RESET_ALL}")
            return
        
        enabled_targets = [t for t in self.config['targets'] if t.get('enabled', True)]
        delay = self.config['settings'].get('delay_between_groups_seconds', 30)
        
        print(f"\n{Fore.CYAN}📤 Sending to {len(enabled_targets)} targets...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Message preview: {message[:50]}...{Style.RESET_ALL}")
        print("-" * 40)
        
        success_count = 0
        for i, target in enumerate(enabled_targets):
            success = await self.send_to_target(target, message)
            if success:
                success_count += 1
            
            # Add delay between sends (except for last one)
            if i < len(enabled_targets) - 1:
                random_delay = delay + random.randint(0, 10)
                await asyncio.sleep(random_delay)
        
        print(f"\n{Fore.GREEN}✓ Completed: {success_count}/{len(enabled_targets)} successful{Style.RESET_ALL}")
        self.logger.info(f"Batch complete: {success_count}/{len(enabled_targets)} successful")
    
    async def send_single(self, target_username: str, message: str):
        """Send a single message to a specific target."""
        target = {'name': target_username, 'username': target_username}
        await self.send_to_target(target, message)
    
    async def run_scheduler(self):
        """Run the automated scheduler."""
        schedule_config = self.config.get('schedule', {})
        interval = schedule_config.get('interval_minutes', 60)
        random_delay = schedule_config.get('random_delay_minutes', 5)
        
        print(f"\n{Fore.CYAN}🔄 Starting scheduler...{Style.RESET_ALL}")
        print(f"   Interval: Every {interval} minutes (+/- {random_delay} min random)")
        print(f"   Active hours: {schedule_config.get('active_hours', {}).get('start', 0)}:00 - {schedule_config.get('active_hours', {}).get('end', 24)}:00")
        print(f"{Fore.YELLOW}   Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        while True:
            try:
                await self.send_to_all()
                
                # Calculate next run time with random delay
                actual_delay = interval + random.randint(-random_delay, random_delay)
                actual_delay = max(5, actual_delay)  # Minimum 5 minutes
                
                next_run = datetime.now() + timedelta(minutes=actual_delay)
                print(f"\n{Fore.CYAN}⏰ Next run at: {next_run.strftime('%H:%M:%S')} ({actual_delay} min){Style.RESET_ALL}")
                
                await asyncio.sleep(actual_delay * 60)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Scheduler stopped by user{Style.RESET_ALL}")
                break


class ConfigManager:
    """Interactive configuration manager."""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or SCRIPT_DIR / CONFIG_FILE
    
    def setup_wizard(self):
        """Interactive setup wizard."""
        print(f"\n{Fore.CYAN}🔧 TELEGRAM MARKETING SETUP WIZARD{Style.RESET_ALL}")
        print("=" * 50)
        
        config = {
            "api_id": "",
            "api_hash": "",
            "phone_number": "",
            "session_name": "marketing_session",
            "targets": [],
            "messages": [],
            "schedule": {
                "enabled": True,
                "interval_minutes": 60,
                "random_delay_minutes": 5,
                "active_hours": {"start": 9, "end": 21},
                "active_days": [0, 1, 2, 3, 4, 5, 6]
            },
            "settings": {
                "rotate_messages": True,
                "delay_between_groups_seconds": 30,
                "max_messages_per_day": 50,
                "log_file": "telegram_marketing.log"
            }
        }
        
        print(f"\n{Fore.YELLOW}Step 1: Get API Credentials{Style.RESET_ALL}")
        print("Go to https://my.telegram.org and create an app")
        print("You'll get api_id and api_hash\n")
        
        config['api_id'] = input("Enter your API ID: ").strip()
        config['api_hash'] = input("Enter your API Hash: ").strip()
        config['phone_number'] = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
        
        print(f"\n{Fore.YELLOW}Step 2: Schedule Settings{Style.RESET_ALL}")
        try:
            interval = input("Message interval in minutes (default 60): ").strip()
            config['schedule']['interval_minutes'] = int(interval) if interval else 60
            
            start_hour = input("Active hours start (0-23, default 9): ").strip()
            config['schedule']['active_hours']['start'] = int(start_hour) if start_hour else 9
            
            end_hour = input("Active hours end (0-23, default 21): ").strip()
            config['schedule']['active_hours']['end'] = int(end_hour) if end_hour else 21
        except ValueError:
            print(f"{Fore.YELLOW}Using default values{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}Step 3: Add Messages{Style.RESET_ALL}")
        print("Enter your marketing messages (empty line to finish):\n")
        
        msg_count = 0
        while True:
            print(f"Message {msg_count + 1} (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            
            if not lines:
                break
            
            message_text = "\n".join(lines)
            config['messages'].append({
                "id": f"msg{msg_count + 1}",
                "text": message_text,
                "enabled": True
            })
            msg_count += 1
            print(f"{Fore.GREEN}✓ Message {msg_count} added{Style.RESET_ALL}\n")
        
        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"\n{Fore.GREEN}✓ Configuration saved to {self.config_path}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print("1. Run: python telegram_marketer.py --login (to authenticate)")
        print("2. Run: python telegram_marketer.py --list (to see your groups)")
        print("3. Edit config.json to add target groups/channels")
        print("4. Run: python telegram_marketer.py --start (to begin automation)")
    
    def add_target(self, name: str, username: str):
        """Add a new target to config."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        config['targets'].append({
            "name": name,
            "username": username,
            "enabled": True
        })
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"{Fore.GREEN}✓ Added target: {name} ({username}){Style.RESET_ALL}")
    
    def add_message(self, message_id: str, text: str):
        """Add a new message to config."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        config['messages'].append({
            "id": message_id,
            "text": text,
            "enabled": True
        })
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"{Fore.GREEN}✓ Added message: {message_id}{Style.RESET_ALL}")
    
    def show_status(self):
        """Show current configuration status."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}Config not found. Run --setup first.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}📊 CONFIGURATION STATUS{Style.RESET_ALL}")
        print("=" * 50)
        
        # API Status
        has_api = all([config.get('api_id'), config.get('api_hash'), config.get('phone_number')])
        api_status = f"{Fore.GREEN}✓ Configured{Style.RESET_ALL}" if has_api else f"{Fore.RED}✗ Missing{Style.RESET_ALL}"
        print(f"API Credentials: {api_status}")
        
        # Targets
        targets = config.get('targets', [])
        enabled_targets = [t for t in targets if t.get('enabled', True)]
        print(f"\n{Fore.YELLOW}Targets: {len(enabled_targets)}/{len(targets)} enabled{Style.RESET_ALL}")
        for t in targets:
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if t.get('enabled', True) else f"{Fore.RED}✗{Style.RESET_ALL}"
            print(f"  {status} {t['name']} ({t.get('username', 'N/A')})")
        
        # Messages
        messages = config.get('messages', [])
        enabled_messages = [m for m in messages if m.get('enabled', True)]
        print(f"\n{Fore.YELLOW}Messages: {len(enabled_messages)}/{len(messages)} enabled{Style.RESET_ALL}")
        for m in messages:
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if m.get('enabled', True) else f"{Fore.RED}✗{Style.RESET_ALL}"
            preview = m['text'][:40] + "..." if len(m['text']) > 40 else m['text']
            print(f"  {status} [{m['id']}] {preview}")
        
        # Schedule
        schedule = config.get('schedule', {})
        print(f"\n{Fore.YELLOW}Schedule:{Style.RESET_ALL}")
        print(f"  Enabled: {schedule.get('enabled', True)}")
        print(f"  Interval: Every {schedule.get('interval_minutes', 60)} minutes")
        hours = schedule.get('active_hours', {})
        print(f"  Active hours: {hours.get('start', 0)}:00 - {hours.get('end', 24)}:00")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Telegram Marketing Automation Tool')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--login', action='store_true', help='Login to Telegram')
    parser.add_argument('--list', action='store_true', help='List available groups/channels')
    parser.add_argument('--start', action='store_true', help='Start automated scheduler')
    parser.add_argument('--send-once', action='store_true', help='Send messages once to all targets')
    parser.add_argument('--send-to', type=str, help='Send message to specific target')
    parser.add_argument('--message', type=str, help='Custom message to send')
    parser.add_argument('--add-target', nargs=2, metavar=('NAME', 'USERNAME'), help='Add target to config')
    parser.add_argument('--add-message', nargs=2, metavar=('ID', 'TEXT'), help='Add message to config')
    parser.add_argument('--status', action='store_true', help='Show current configuration status')
    parser.add_argument('--config', type=str, help='Path to config file')
    
    args = parser.parse_args()
    
    config_path = args.config if args.config else None
    
    # Config manager operations (don't need Telegram connection)
    config_manager = ConfigManager(config_path)
    
    if args.setup:
        config_manager.setup_wizard()
        return
    
    if args.add_target:
        config_manager.add_target(args.add_target[0], args.add_target[1])
        return
    
    if args.add_message:
        config_manager.add_message(args.add_message[0], args.add_message[1])
        return
    
    if args.status:
        config_manager.show_status()
        return
    
    # Telegram operations (need connection)
    marketer = TelegramMarketer(config_path)
    marketer._print_banner()
    
    if not await marketer.connect():
        return
    
    try:
        if args.login:
            print(f"{Fore.GREEN}✓ Successfully logged in!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Session saved. You won't need to login again.{Style.RESET_ALL}")
        
        elif args.list:
            await marketer.list_dialogs()
        
        elif args.send_to:
            message = args.message or marketer._get_next_message()
            if message:
                await marketer.send_single(args.send_to, message)
            else:
                print(f"{Fore.RED}No message to send. Add messages to config or use --message{Style.RESET_ALL}")
        
        elif args.send_once:
            await marketer.send_to_all()
        
        elif args.start:
            await marketer.run_scheduler()
        
        else:
            parser.print_help()
            print(f"\n{Fore.CYAN}Quick start:{Style.RESET_ALL}")
            print("  1. python telegram_marketer.py --setup")
            print("  2. python telegram_marketer.py --login")
            print("  3. python telegram_marketer.py --list")
            print("  4. python telegram_marketer.py --start")
    
    finally:
        await marketer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
