#!/usr/bin/env python3
"""
WhatsApp Business API Marketing Automation Tool
================================================
Automated message sender for WhatsApp groups and broadcasts using the official API.
Author: TechyEra Marketing Suite

Supports:
- WhatsApp Business Cloud API (Meta)
- Message templates and free-form messages
- Groups and Broadcast lists
- Scheduled sending with frequency control
- Rate limiting and safety features
"""

import json
import asyncio
import aiohttp
import random
import logging
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    # Fallback if colorama not installed
    class Fore:
        RED = GREEN = YELLOW = CYAN = BLUE = MAGENTA = ""
    class Style:
        RESET_ALL = ""

# Constants
CONFIG_FILE = "config.json"
SCRIPT_DIR = Path(__file__).parent


class MessageType(Enum):
    TEXT = "text"
    TEMPLATE = "template"
    IMAGE = "image"
    DOCUMENT = "document"


@dataclass
class APIResponse:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[dict] = None


class WhatsAppAPIMarketer:
    """Main class for WhatsApp Business API marketing automation."""
    
    # WhatsApp Cloud API Base URL
    API_BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else SCRIPT_DIR / CONFIG_FILE
        self.config = self._load_config()
        self.session: Optional[aiohttp.ClientSession] = None
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
            print(f"{Fore.YELLOW}Run 'python whatsapp_api_marketer.py --setup' to create one.{Style.RESET_ALL}")
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
        log_file = self.config.get('settings', {}).get('log_file', 'whatsapp_marketing.log')
        log_path = SCRIPT_DIR / 'logs' / log_file
        log_path.parent.mkdir(exist_ok=True)
        
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
{Fore.GREEN}╔══════════════════════════════════════════════════════════╗
║         📱 WHATSAPP BUSINESS API MARKETING 📱             ║
║                    TechyEra Suite                          ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
    
    @property
    def phone_number_id(self) -> str:
        """Get the WhatsApp Business Phone Number ID."""
        return self.config.get('phone_number_id', '')
    
    @property
    def access_token(self) -> str:
        """Get the API access token."""
        return self.config.get('access_token', '')
    
    @property
    def api_headers(self) -> dict:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def _init_session(self):
        """Initialize aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def verify_credentials(self) -> bool:
        """Verify API credentials are valid."""
        if not self.phone_number_id or not self.access_token:
            print(f"{Fore.RED}Missing API credentials in config.json{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please fill in phone_number_id and access_token{Style.RESET_ALL}")
            return False
        
        await self._init_session()
        
        # Test API with a simple request
        url = f"{self.API_BASE_URL}/{self.phone_number_id}"
        
        try:
            async with self.session.get(url, headers=self.api_headers) as response:
                if response.status == 200:
                    data = await response.json()
                    phone = data.get('display_phone_number', 'Unknown')
                    print(f"{Fore.GREEN}✓ Connected - Phone: {phone}{Style.RESET_ALL}")
                    self.logger.info(f"API verified - Phone: {phone}")
                    return True
                else:
                    error = await response.text()
                    print(f"{Fore.RED}API Error: {error}{Style.RESET_ALL}")
                    return False
        except Exception as e:
            print(f"{Fore.RED}Connection failed: {e}{Style.RESET_ALL}")
            self.logger.error(f"Connection failed: {e}")
            return False
    
    async def send_text_message(self, recipient: str, message: str) -> APIResponse:
        """
        Send a text message to a recipient.
        
        Args:
            recipient: Phone number with country code (e.g., 919876543210)
            message: Message text to send
        
        Returns:
            APIResponse with success status and message ID
        """
        await self._init_session()
        
        url = f"{self.API_BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message
            }
        }
        
        try:
            async with self.session.post(url, headers=self.api_headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    msg_id = data.get('messages', [{}])[0].get('id', '')
                    return APIResponse(success=True, message_id=msg_id, raw_response=data)
                else:
                    error = data.get('error', {}).get('message', str(data))
                    return APIResponse(success=False, error=error, raw_response=data)
                    
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    async def send_template_message(
        self, 
        recipient: str, 
        template_name: str, 
        language_code: str = "en",
        components: List[dict] = None
    ) -> APIResponse:
        """
        Send a template message (required for non-opted-in users).
        
        Args:
            recipient: Phone number with country code
            template_name: Name of the approved template
            language_code: Language code (e.g., "en", "hi")
            components: Template components (header, body parameters)
        
        Returns:
            APIResponse with success status
        """
        await self._init_session()
        
        url = f"{self.API_BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            async with self.session.post(url, headers=self.api_headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    msg_id = data.get('messages', [{}])[0].get('id', '')
                    return APIResponse(success=True, message_id=msg_id, raw_response=data)
                else:
                    error = data.get('error', {}).get('message', str(data))
                    return APIResponse(success=False, error=error, raw_response=data)
                    
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    async def send_image_message(
        self, 
        recipient: str, 
        image_url: str = None,
        image_id: str = None,
        caption: str = None
    ) -> APIResponse:
        """
        Send an image message.
        
        Args:
            recipient: Phone number with country code
            image_url: Public URL of the image (or use image_id)
            image_id: Media ID of uploaded image
            caption: Optional caption for the image
        
        Returns:
            APIResponse with success status
        """
        await self._init_session()
        
        url = f"{self.API_BASE_URL}/{self.phone_number_id}/messages"
        
        image_data = {}
        if image_url:
            image_data["link"] = image_url
        elif image_id:
            image_data["id"] = image_id
        
        if caption:
            image_data["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "image",
            "image": image_data
        }
        
        try:
            async with self.session.post(url, headers=self.api_headers, json=payload) as response:
                data = await response.json()
                
                if response.status == 200:
                    msg_id = data.get('messages', [{}])[0].get('id', '')
                    return APIResponse(success=True, message_id=msg_id, raw_response=data)
                else:
                    error = data.get('error', {}).get('message', str(data))
                    return APIResponse(success=False, error=error, raw_response=data)
                    
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    async def upload_media(self, file_path: str, media_type: str = "image/jpeg") -> Optional[str]:
        """
        Upload media file to WhatsApp servers.
        
        Args:
            file_path: Path to the media file
            media_type: MIME type of the file
        
        Returns:
            Media ID if successful, None otherwise
        """
        await self._init_session()
        
        url = f"{self.API_BASE_URL}/{self.phone_number_id}/media"
        
        try:
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename=Path(file_path).name, content_type=media_type)
                form.add_field('messaging_product', 'whatsapp')
                form.add_field('type', media_type)
                
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                async with self.session.post(url, headers=headers, data=form) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        return data.get('id')
                    else:
                        self.logger.error(f"Media upload failed: {data}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Media upload error: {e}")
            return None
    
    def _get_next_message(self) -> Optional[Dict]:
        """Get the next message to send (rotation support)."""
        enabled_messages = [m for m in self.config.get('messages', []) if m.get('enabled', True)]
        
        if not enabled_messages:
            return None
        
        if self.config.get('settings', {}).get('rotate_messages', True):
            message = enabled_messages[self.message_index % len(enabled_messages)]
            self.message_index += 1
        else:
            message = random.choice(enabled_messages)
        
        return message
    
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
        
        max_daily = self.config.get('settings', {}).get('max_messages_per_day', 1000)
        return self.messages_sent_today < max_daily
    
    async def send_to_target(self, target: dict, message_config: dict) -> bool:
        """
        Send message to a single target.
        
        Args:
            target: Target configuration (phone, name, type)
            message_config: Message configuration (text, type, template_name)
        
        Returns:
            True if successful, False otherwise
        """
        phone = target.get('phone', '').replace('+', '').replace(' ', '').replace('-', '')
        name = target.get('name', phone)
        
        try:
            msg_type = message_config.get('type', 'text')
            
            if msg_type == 'template':
                response = await self.send_template_message(
                    recipient=phone,
                    template_name=message_config.get('template_name', 'hello_world'),
                    language_code=message_config.get('language', 'en'),
                    components=message_config.get('components')
                )
            elif msg_type == 'image':
                text = message_config.get('text', '')
                # Personalize message if enabled
                if self.config.get('settings', {}).get('personalize', False):
                    text = text.replace('{{name}}', target.get('name', 'there'))
                
                response = await self.send_image_message(
                    recipient=phone,
                    image_url=message_config.get('image_url'),
                    image_id=message_config.get('image_id'),
                    caption=text
                )
            else:
                text = message_config.get('text', '')
                # Personalize message if enabled
                if self.config.get('settings', {}).get('personalize', False):
                    text = text.replace('{{name}}', target.get('name', 'there'))
                
                response = await self.send_text_message(recipient=phone, message=text)
            
            if response.success:
                self.messages_sent_today += 1
                print(f"{Fore.GREEN}✓ Sent to: {name} ({phone}){Style.RESET_ALL}")
                self.logger.info(f"Message sent to {name} ({phone}) - ID: {response.message_id}")
                return True
            else:
                print(f"{Fore.RED}✗ Failed: {name} - {response.error}{Style.RESET_ALL}")
                self.logger.warning(f"Failed to send to {name}: {response.error}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}✗ Error sending to {name}: {e}{Style.RESET_ALL}")
            self.logger.error(f"Error sending to {name}: {e}")
            return False
    
    async def send_to_broadcast(self, broadcast: dict, message_config: dict) -> Dict[str, int]:
        """
        Send message to a broadcast list (multiple recipients).
        
        Args:
            broadcast: Broadcast configuration with list of recipients
            message_config: Message configuration
        
        Returns:
            Dict with success and failure counts
        """
        recipients = broadcast.get('recipients', [])
        name = broadcast.get('name', 'Broadcast')
        delay = self.config.get('settings', {}).get('delay_between_messages_seconds', 2)
        
        print(f"\n{Fore.CYAN}📤 Sending to broadcast: {name} ({len(recipients)} recipients){Style.RESET_ALL}")
        
        results = {"success": 0, "failed": 0}
        
        for i, recipient in enumerate(recipients):
            if not self._check_daily_limit():
                print(f"{Fore.YELLOW}⚠ Daily limit reached. Stopping.{Style.RESET_ALL}")
                break
            
            target = {"phone": recipient.get('phone'), "name": recipient.get('name', recipient.get('phone'))}
            success = await self.send_to_target(target, message_config)
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            # Add delay between messages
            if i < len(recipients) - 1:
                random_delay = delay + random.uniform(0, 2)
                await asyncio.sleep(random_delay)
        
        return results
    
    async def send_to_all(self):
        """Send message to all enabled targets and broadcasts."""
        if not self._is_within_active_hours():
            print(f"{Fore.YELLOW}⏰ Outside active hours. Skipping...{Style.RESET_ALL}")
            return
        
        if not self._check_daily_limit():
            print(f"{Fore.YELLOW}📊 Daily limit reached. Waiting until tomorrow...{Style.RESET_ALL}")
            return
        
        message_config = self._get_next_message()
        if not message_config:
            print(f"{Fore.RED}No enabled messages in config{Style.RESET_ALL}")
            return
        
        # Get enabled targets (individual contacts)
        enabled_targets = [t for t in self.config.get('targets', []) if t.get('enabled', True)]
        
        # Get enabled broadcasts
        enabled_broadcasts = [b for b in self.config.get('broadcasts', []) if b.get('enabled', True)]
        
        delay = self.config.get('settings', {}).get('delay_between_groups_seconds', 30)
        
        total_recipients = len(enabled_targets) + sum(len(b.get('recipients', [])) for b in enabled_broadcasts)
        
        print(f"\n{Fore.CYAN}📤 Sending campaign...{Style.RESET_ALL}")
        print(f"   Targets: {len(enabled_targets)}")
        print(f"   Broadcasts: {len(enabled_broadcasts)} ({total_recipients - len(enabled_targets)} recipients)")
        print(f"   Message: {message_config.get('text', message_config.get('template_name', 'N/A'))[:50]}...")
        print("-" * 40)
        
        success_count = 0
        fail_count = 0
        
        # Send to individual targets
        for i, target in enumerate(enabled_targets):
            if not self._check_daily_limit():
                break
                
            success = await self.send_to_target(target, message_config)
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            if i < len(enabled_targets) - 1:
                random_delay = delay + random.randint(0, 5)
                await asyncio.sleep(random_delay)
        
        # Send to broadcasts
        for i, broadcast in enumerate(enabled_broadcasts):
            if not self._check_daily_limit():
                break
            
            results = await self.send_to_broadcast(broadcast, message_config)
            success_count += results["success"]
            fail_count += results["failed"]
            
            if i < len(enabled_broadcasts) - 1:
                random_delay = delay + random.randint(0, 10)
                await asyncio.sleep(random_delay)
        
        print(f"\n{Fore.GREEN}✓ Completed: {success_count} successful, {fail_count} failed{Style.RESET_ALL}")
        self.logger.info(f"Batch complete: {success_count} successful, {fail_count} failed")
    
    async def send_single(self, phone: str, message: str):
        """Send a single message to a specific phone number."""
        target = {'name': phone, 'phone': phone}
        message_config = {'type': 'text', 'text': message}
        await self.send_to_target(target, message_config)
    
    async def run_scheduler(self):
        """Run the automated scheduler."""
        schedule_config = self.config.get('schedule', {})
        interval = schedule_config.get('interval_minutes', 60)
        random_delay = schedule_config.get('random_delay_minutes', 5)
        
        print(f"\n{Fore.CYAN}🔄 Starting scheduler...{Style.RESET_ALL}")
        print(f"   Interval: Every {interval} minutes (+/- {random_delay} min random)")
        hours = schedule_config.get('active_hours', {})
        print(f"   Active hours: {hours.get('start', 0)}:00 - {hours.get('end', 24)}:00")
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
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                print(f"{Fore.RED}Error: {e}. Retrying in 5 minutes...{Style.RESET_ALL}")
                await asyncio.sleep(300)
    
    async def list_templates(self):
        """List available message templates."""
        await self._init_session()
        
        waba_id = self.config.get('waba_id', '')
        if not waba_id:
            print(f"{Fore.YELLOW}Note: Set 'waba_id' in config to list templates{Style.RESET_ALL}")
            return []
        
        url = f"{self.API_BASE_URL}/{waba_id}/message_templates"
        
        try:
            async with self.session.get(url, headers=self.api_headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    templates = data.get('data', [])
                    print(f"\n{Fore.CYAN}📋 Available Templates ({len(templates)}):{Style.RESET_ALL}")
                    print("-" * 60)
                    
                    for t in templates:
                        status = t.get('status', 'UNKNOWN')
                        status_color = Fore.GREEN if status == 'APPROVED' else Fore.YELLOW
                        print(f"  • {t['name']} [{status_color}{status}{Style.RESET_ALL}]")
                        print(f"    Language: {t.get('language', 'N/A')}")
                        print(f"    Category: {t.get('category', 'N/A')}")
                    
                    return templates
                else:
                    print(f"{Fore.RED}Failed to get templates: {data}{Style.RESET_ALL}")
                    return []
                    
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            return []


class ConfigManager:
    """Interactive configuration manager."""
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else SCRIPT_DIR / CONFIG_FILE
    
    def setup_wizard(self):
        """Interactive setup wizard."""
        print(f"\n{Fore.GREEN}🔧 WHATSAPP BUSINESS API SETUP WIZARD{Style.RESET_ALL}")
        print("=" * 50)
        
        config = {
            "phone_number_id": "",
            "access_token": "",
            "waba_id": "",
            "targets": [],
            "broadcasts": [],
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
                "personalize": False,
                "delay_between_groups_seconds": 30,
                "delay_between_messages_seconds": 2,
                "max_messages_per_day": 1000,
                "log_file": "whatsapp_marketing.log"
            }
        }
        
        print(f"\n{Fore.YELLOW}Step 1: Get WhatsApp Business API Credentials{Style.RESET_ALL}")
        print("Go to https://developers.facebook.com/apps/ and:")
        print("1. Create or select a Business App")
        print("2. Add WhatsApp product")
        print("3. Get your Phone Number ID and Access Token\n")
        
        config['phone_number_id'] = input("Enter your Phone Number ID: ").strip()
        config['access_token'] = input("Enter your Access Token: ").strip()
        config['waba_id'] = input("Enter your WABA ID (optional, for templates): ").strip()
        
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
                "type": "text",
                "text": message_text,
                "enabled": True
            })
            msg_count += 1
            print(f"{Fore.GREEN}✓ Message {msg_count} added{Style.RESET_ALL}\n")
        
        # Add example broadcast
        config['broadcasts'].append({
            "name": "Example Broadcast",
            "enabled": False,
            "recipients": [
                {"phone": "919876543210", "name": "Example Contact"}
            ]
        })
        
        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"\n{Fore.GREEN}✓ Configuration saved to {self.config_path}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print("1. Run: python whatsapp_api_marketer.py --verify (to test credentials)")
        print("2. Edit config.json to add target phone numbers and broadcasts")
        print("3. Run: python whatsapp_api_marketer.py --send-once (to test)")
        print("4. Run: python whatsapp_api_marketer.py --start (to begin automation)")
    
    def add_target(self, name: str, phone: str):
        """Add a new target to config."""
        config = self._load_config()
        
        config['targets'].append({
            "name": name,
            "phone": phone,
            "enabled": True
        })
        
        self._save_config(config)
        print(f"{Fore.GREEN}✓ Added target: {name} ({phone}){Style.RESET_ALL}")
    
    def add_broadcast(self, name: str, phones: List[str]):
        """Add a new broadcast list to config."""
        config = self._load_config()
        
        recipients = [{"phone": p, "name": f"Contact {i+1}"} for i, p in enumerate(phones)]
        
        config['broadcasts'].append({
            "name": name,
            "recipients": recipients,
            "enabled": True
        })
        
        self._save_config(config)
        print(f"{Fore.GREEN}✓ Added broadcast: {name} with {len(phones)} recipients{Style.RESET_ALL}")
    
    def add_message(self, message_id: str, text: str, msg_type: str = "text"):
        """Add a new message to config."""
        config = self._load_config()
        
        config['messages'].append({
            "id": message_id,
            "type": msg_type,
            "text": text,
            "enabled": True
        })
        
        self._save_config(config)
        print(f"{Fore.GREEN}✓ Added message: {message_id}{Style.RESET_ALL}")
    
    def _load_config(self) -> dict:
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_config(self, config: dict):
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
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
        has_api = all([config.get('phone_number_id'), config.get('access_token')])
        api_status = f"{Fore.GREEN}✓ Configured{Style.RESET_ALL}" if has_api else f"{Fore.RED}✗ Missing{Style.RESET_ALL}"
        print(f"API Credentials: {api_status}")
        
        if config.get('phone_number_id'):
            print(f"   Phone Number ID: {config['phone_number_id'][:10]}...")
        
        # Targets
        targets = config.get('targets', [])
        enabled_targets = [t for t in targets if t.get('enabled', True)]
        print(f"\n{Fore.YELLOW}Individual Targets: {len(enabled_targets)}/{len(targets)} enabled{Style.RESET_ALL}")
        for t in targets[:10]:
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if t.get('enabled', True) else f"{Fore.RED}✗{Style.RESET_ALL}"
            print(f"  {status} {t.get('name', 'N/A')} ({t.get('phone', 'N/A')})")
        if len(targets) > 10:
            print(f"  ... and {len(targets) - 10} more")
        
        # Broadcasts
        broadcasts = config.get('broadcasts', [])
        enabled_broadcasts = [b for b in broadcasts if b.get('enabled', True)]
        total_recipients = sum(len(b.get('recipients', [])) for b in broadcasts)
        print(f"\n{Fore.YELLOW}Broadcasts: {len(enabled_broadcasts)}/{len(broadcasts)} enabled ({total_recipients} total recipients){Style.RESET_ALL}")
        for b in broadcasts:
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if b.get('enabled', True) else f"{Fore.RED}✗{Style.RESET_ALL}"
            print(f"  {status} {b['name']} ({len(b.get('recipients', []))} recipients)")
        
        # Messages
        messages = config.get('messages', [])
        enabled_messages = [m for m in messages if m.get('enabled', True)]
        print(f"\n{Fore.YELLOW}Messages: {len(enabled_messages)}/{len(messages)} enabled{Style.RESET_ALL}")
        for m in messages:
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if m.get('enabled', True) else f"{Fore.RED}✗{Style.RESET_ALL}"
            msg_type = m.get('type', 'text')
            preview = m.get('text', m.get('template_name', 'N/A'))[:40]
            print(f"  {status} [{m.get('id', 'N/A')}] ({msg_type}) {preview}...")
        
        # Schedule
        schedule = config.get('schedule', {})
        print(f"\n{Fore.YELLOW}Schedule:{Style.RESET_ALL}")
        print(f"  Enabled: {schedule.get('enabled', True)}")
        print(f"  Interval: Every {schedule.get('interval_minutes', 60)} minutes")
        hours = schedule.get('active_hours', {})
        print(f"  Active hours: {hours.get('start', 0)}:00 - {hours.get('end', 24)}:00")
        
        # Settings
        settings = config.get('settings', {})
        print(f"\n{Fore.YELLOW}Settings:{Style.RESET_ALL}")
        print(f"  Max messages/day: {settings.get('max_messages_per_day', 1000)}")
        print(f"  Rotate messages: {settings.get('rotate_messages', True)}")
        print(f"  Personalize: {settings.get('personalize', False)}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='WhatsApp Business API Marketing Tool')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--verify', action='store_true', help='Verify API credentials')
    parser.add_argument('--start', action='store_true', help='Start automated scheduler')
    parser.add_argument('--send-once', action='store_true', help='Send messages once to all targets')
    parser.add_argument('--send-to', type=str, help='Send message to specific phone number')
    parser.add_argument('--message', type=str, help='Custom message to send')
    parser.add_argument('--add-target', nargs=2, metavar=('NAME', 'PHONE'), help='Add target to config')
    parser.add_argument('--add-broadcast', nargs='+', metavar=('NAME', 'PHONES'), help='Add broadcast list')
    parser.add_argument('--add-message', nargs=2, metavar=('ID', 'TEXT'), help='Add message to config')
    parser.add_argument('--templates', action='store_true', help='List available templates')
    parser.add_argument('--status', action='store_true', help='Show current configuration status')
    parser.add_argument('--config', type=str, help='Path to config file')
    
    args = parser.parse_args()
    
    config_path = args.config if args.config else None
    
    # Config manager operations (don't need API connection)
    config_manager = ConfigManager(config_path)
    
    if args.setup:
        config_manager.setup_wizard()
        return
    
    if args.add_target:
        config_manager.add_target(args.add_target[0], args.add_target[1])
        return
    
    if args.add_broadcast:
        if len(args.add_broadcast) < 2:
            print(f"{Fore.RED}Usage: --add-broadcast NAME PHONE1 PHONE2 ...{Style.RESET_ALL}")
            return
        config_manager.add_broadcast(args.add_broadcast[0], args.add_broadcast[1:])
        return
    
    if args.add_message:
        config_manager.add_message(args.add_message[0], args.add_message[1])
        return
    
    if args.status:
        config_manager.show_status()
        return
    
    # API operations (need connection)
    marketer = WhatsAppAPIMarketer(config_path)
    marketer._print_banner()
    
    try:
        if args.verify:
            success = await marketer.verify_credentials()
            if success:
                print(f"{Fore.GREEN}✓ API credentials are valid!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ API credentials are invalid or missing{Style.RESET_ALL}")
        
        elif args.templates:
            await marketer.verify_credentials()
            await marketer.list_templates()
        
        elif args.send_to:
            if not await marketer.verify_credentials():
                return
            message = args.message or marketer._get_next_message()
            if message:
                msg_text = message if isinstance(message, str) else message.get('text', '')
                await marketer.send_single(args.send_to, msg_text)
            else:
                print(f"{Fore.RED}No message to send. Add messages to config or use --message{Style.RESET_ALL}")
        
        elif args.send_once:
            if not await marketer.verify_credentials():
                return
            await marketer.send_to_all()
        
        elif args.start:
            if not await marketer.verify_credentials():
                return
            await marketer.run_scheduler()
        
        else:
            parser.print_help()
            print(f"\n{Fore.CYAN}Quick start:{Style.RESET_ALL}")
            print("  1. python whatsapp_api_marketer.py --setup")
            print("  2. python whatsapp_api_marketer.py --verify")
            print("  3. Edit config.json to add targets/broadcasts")
            print("  4. python whatsapp_api_marketer.py --send-once")
            print("  5. python whatsapp_api_marketer.py --start")
    
    finally:
        await marketer._close_session()


if __name__ == "__main__":
    asyncio.run(main())
