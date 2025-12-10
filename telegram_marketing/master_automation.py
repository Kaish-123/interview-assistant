#!/usr/bin/env python3
"""
MASTER AUTOMATION - Complete Telegram Marketing Automation
============================================================
This is the MAIN script that handles EVERYTHING:
1. Sends messages to all groups every hour
2. Finds new groups daily
3. Joins new groups automatically
4. Adds them to config automatically
5. Runs 24/7 with smart scheduling

Just run this ONE script and forget about it!
"""

import asyncio
import json
import random
import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel
from colorama import init, Fore, Style

init()

# Configuration
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
STATE_FILE = SCRIPT_DIR / "automation_state.json"

# Timing settings
MESSAGE_INTERVAL_MINUTES = 60
GROWTH_INTERVAL_HOURS = 6  # Find & join new groups every 6 hours
MAX_JOINS_PER_CYCLE = 3    # Join max 3 groups per cycle (avoid rate limits)

# Search keywords
SEARCH_KEYWORDS = [
    "proxy interview", "interview proxy", "job support", "interview support",
    "data engineer", "data analyst", "full stack developer", "python developer",
    "java developer", "devops jobs", "IT jobs USA", "software developer",
    "tech jobs", "fresher IT jobs", "IT placement", "developer jobs",
    "aws jobs", "azure jobs", "cloud jobs", "remote developer",
    "web developer", "backend developer", "frontend developer"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(SCRIPT_DIR / "master_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramMasterBot:
    def __init__(self):
        self.config = self._load_config()
        self.state = self._load_state()
        self.client = None
        self.running = True
        self.message_index = 0
        
    def _load_config(self):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    
    def _save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def _load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            "last_message_batch": None,
            "last_growth_run": None,
            "messages_sent_today": 0,
            "groups_joined_today": 0,
            "total_messages_sent": 0,
            "total_groups_joined": 0,
            "known_groups": []
        }
    
    def _save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    async def connect(self):
        """Connect to Telegram."""
        self.client = TelegramClient(
            str(SCRIPT_DIR / "master_session"),
            self.config['api_id'],
            self.config['api_hash']
        )
        await self.client.start(phone=self.config['phone_number'])
        me = await self.client.get_me()
        logger.info(f"Connected as: {me.first_name}")
        return True
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
    
    def _get_next_message(self):
        """Get next message to send."""
        enabled = [m for m in self.config['messages'] if m.get('enabled', True)]
        if not enabled:
            return None
        msg = enabled[self.message_index % len(enabled)]
        self.message_index += 1
        return msg['text']
    
    def _get_existing_usernames(self):
        """Get set of existing target usernames."""
        return {t.get('username', '').lower() for t in self.config['targets']}
    
    async def send_messages(self):
        """Send messages to all groups."""
        message = self._get_next_message()
        if not message:
            logger.warning("No messages configured")
            return
        
        enabled_targets = [t for t in self.config['targets'] if t.get('enabled', True)]
        delay = self.config['settings'].get('delay_between_groups_seconds', 30)
        
        logger.info(f"Sending to {len(enabled_targets)} targets...")
        print(f"\n{Fore.CYAN}📤 Sending to {len(enabled_targets)} targets...{Style.RESET_ALL}")
        
        success = 0
        for i, target in enumerate(enabled_targets):
            target_id = target.get('username')
            try:
                if target_id.startswith('@'):
                    entity = await self.client.get_entity(target_id)
                elif target_id.startswith('ID:'):
                    entity = await self.client.get_entity(int(target_id[3:]))
                else:
                    entity = await self.client.get_entity(target_id)
                
                await self.client.send_message(entity, message)
                success += 1
                print(f"{Fore.GREEN}✓ Sent to: {target['name'][:40]}{Style.RESET_ALL}")
                logger.info(f"Sent to {target['name']}")
                
            except errors.FloodWaitError as e:
                logger.warning(f"Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
                
            except errors.ChatWriteForbiddenError:
                print(f"{Fore.RED}✗ No permission: {target['name'][:40]}{Style.RESET_ALL}")
                
            except Exception as e:
                print(f"{Fore.RED}✗ Error: {target['name'][:30]} - {str(e)[:30]}{Style.RESET_ALL}")
            
            if i < len(enabled_targets) - 1:
                await asyncio.sleep(delay + random.randint(0, 15))
        
        self.state['last_message_batch'] = datetime.now().isoformat()
        self.state['messages_sent_today'] += success
        self.state['total_messages_sent'] += success
        self._save_state()
        
        print(f"\n{Fore.GREEN}✅ Completed: {success}/{len(enabled_targets)} successful{Style.RESET_ALL}")
        logger.info(f"Batch complete: {success}/{len(enabled_targets)}")
        
        return success
    
    async def find_and_join_groups(self):
        """Find new groups and join them."""
        print(f"\n{Fore.CYAN}🔍 GROWTH MODE: Finding new groups...{Style.RESET_ALL}")
        logger.info("Starting growth cycle")
        
        existing = self._get_existing_usernames()
        found_groups = []
        
        # Search for groups
        keywords = random.sample(SEARCH_KEYWORDS, min(10, len(SEARCH_KEYWORDS)))
        for keyword in keywords:
            try:
                result = await self.client(SearchRequest(q=keyword, limit=20))
                for chat in result.chats:
                    if isinstance(chat, Channel) and chat.megagroup:
                        username = f"@{chat.username}" if chat.username else None
                        if username and username.lower() not in existing:
                            if username.lower() not in [g['username'].lower() for g in found_groups]:
                                members = getattr(chat, 'participants_count', 0) or 0
                                found_groups.append({
                                    'title': chat.title,
                                    'username': username,
                                    'members': members
                                })
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Search error: {e}")
        
        # Sort by members
        found_groups.sort(key=lambda x: x.get('members', 0), reverse=True)
        print(f"{Fore.YELLOW}Found {len(found_groups)} new groups{Style.RESET_ALL}")
        
        # Join top groups
        joined = 0
        for group in found_groups[:MAX_JOINS_PER_CYCLE]:
            try:
                print(f"  Joining {group['username']}...", end=" ")
                entity = await self.client.get_entity(group['username'])
                await self.client(JoinChannelRequest(entity))
                print(f"{Fore.GREEN}✅ Joined!{Style.RESET_ALL}")
                
                # Add to config
                self.config['targets'].append({
                    'name': f"{group['title'][:35]} ({group.get('members', '?')})",
                    'username': group['username'],
                    'enabled': True
                })
                joined += 1
                
                await asyncio.sleep(random.randint(20, 40))
                
            except errors.FloodWaitError as e:
                print(f"{Fore.YELLOW}⏰ Rate limited{Style.RESET_ALL}")
                logger.warning(f"Rate limited during join: {e.seconds}s")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Failed{Style.RESET_ALL}")
        
        if joined > 0:
            self._save_config()
            self.state['groups_joined_today'] += joined
            self.state['total_groups_joined'] += joined
        
        self.state['last_growth_run'] = datetime.now().isoformat()
        self._save_state()
        
        print(f"\n{Fore.GREEN}✅ Joined {joined} new groups. Total targets: {len(self.config['targets'])}{Style.RESET_ALL}")
        logger.info(f"Growth complete: joined {joined} groups")
        
        return joined
    
    def _should_run_growth(self):
        """Check if we should run growth cycle."""
        last_run = self.state.get('last_growth_run')
        if not last_run:
            return True
        
        last_time = datetime.fromisoformat(last_run)
        hours_passed = (datetime.now() - last_time).total_seconds() / 3600
        return hours_passed >= GROWTH_INTERVAL_HOURS
    
    def _reset_daily_stats(self):
        """Reset daily stats at midnight."""
        now = datetime.now()
        if now.hour == 0 and now.minute < 5:
            self.state['messages_sent_today'] = 0
            self.state['groups_joined_today'] = 0
    
    async def run_forever(self):
        """Main loop - runs forever."""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║       🚀 TECHYERA MASTER AUTOMATION - RUNNING 24/7 🚀      ║
╠══════════════════════════════════════════════════════════╣
║  • Messages: Every {MESSAGE_INTERVAL_MINUTES} minutes                              ║
║  • Growth: Every {GROWTH_INTERVAL_HOURS} hours (find & join new groups)          ║
║  • Targets: {len(self.config['targets']):3} groups                                      ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)
        
        while self.running:
            try:
                self._reset_daily_stats()
                
                # Send messages
                await self.send_messages()
                
                # Check if growth cycle should run
                if self._should_run_growth():
                    await self.find_and_join_groups()
                    # Reload config in case it was updated
                    self.config = self._load_config()
                
                # Calculate next run
                delay = MESSAGE_INTERVAL_MINUTES + random.randint(-5, 5)
                next_run = datetime.now() + timedelta(minutes=delay)
                
                print(f"\n{Fore.CYAN}⏰ Next message batch: {next_run.strftime('%H:%M:%S')} ({delay} min){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}📊 Today: {self.state['messages_sent_today']} msgs, {self.state['groups_joined_today']} new groups{Style.RESET_ALL}")
                
                # Sleep
                await asyncio.sleep(delay * 60)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the bot."""
        await self.connect()
        await self.run_forever()
        await self.disconnect()


def signal_handler(sig, frame):
    print(f"\n{Fore.YELLOW}Shutting down gracefully...{Style.RESET_ALL}")
    sys.exit(0)


async def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bot = TelegramMasterBot()
    await bot.start()


if __name__ == "__main__":
    print(f"{Fore.GREEN}Starting TechyEra Master Automation...{Style.RESET_ALL}")
    asyncio.run(main())
