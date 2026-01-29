#!/usr/bin/env python3
"""Telegram Service Layer"""
import logging
from typing import Optional, Dict, Any, List
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, ChatWriteForbiddenError, ChannelPrivateError,
    UserBannedInChannelError, ChatAdminRequiredError, SessionPasswordNeededError
)
from telethon.tl.types import Channel, Chat, User

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, api_id: int, api_hash: str, session_name: str = "web_session"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.phone_code_hash: Optional[str] = None
    
    async def connect(self):
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.connect()
            self.is_connected = True
            logger.info("Connected to Telegram")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            raise
    
    async def ensure_connected(self):
        if not self.client:
            await self.connect()
            return
        try:
            if not self.client.is_connected():
                logger.info("Reconnecting...")
                await self.client.connect()
                self.is_connected = True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.connect()
            self.is_connected = True
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
    
    async def is_authorized(self) -> bool:
        if not self.client:
            return False
        return await self.client.is_user_authorized()
    
    async def send_code(self, phone: str) -> str:
        if not self.client:
            raise Exception("Not connected")
        result = await self.client.send_code_request(phone)
        self.phone_code_hash = result.phone_code_hash
        return result.phone_code_hash
    
    async def sign_in(self, phone: str, code: str, password: Optional[str] = None) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Not connected")
        try:
            if password:
                user = await self.client.sign_in(password=password)
            else:
                user = await self.client.sign_in(phone=phone, code=code, phone_code_hash=self.phone_code_hash)
            return {"id": user.id, "first_name": user.first_name, "username": user.username}
        except SessionPasswordNeededError:
            raise Exception("Two-factor authentication required")
    
    async def send_message(self, target: str, message: str) -> Dict[str, Any]:
        if not self.client:
            return {"success": False, "error": "Not connected"}
        try:
            await self.ensure_connected()
            if not target.startswith("@"):
                target = f"@{target}"
            entity = await self.client.get_entity(target)
            await self.client.send_message(entity, message)
            logger.info(f"Message sent to {target}")
            return {"success": True, "target": target}
        except FloodWaitError as e:
            return {"success": False, "error": f"Rate limited. Wait {e.seconds}s"}
        except ChatWriteForbiddenError:
            return {"success": False, "error": "Cannot write to this chat"}
        except ChannelPrivateError:
            return {"success": False, "error": "Channel is private"}
        except Exception as e:
            error_str = str(e).lower()
            if "disconnect" in error_str:
                try:
                    await self.ensure_connected()
                    entity = await self.client.get_entity(target)
                    await self.client.send_message(entity, message)
                    return {"success": True, "target": target}
                except Exception as retry_e:
                    return {"success": False, "error": str(retry_e)}
            return {"success": False, "error": str(e)}
    
    async def search_public(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            await self.ensure_connected()
            from telethon.tl.functions.contacts import SearchRequest
            result = await self.client(SearchRequest(q=query, limit=limit))
            groups = []
            for chat in result.chats:
                if hasattr(chat, 'username') and chat.username:
                    groups.append({
                        "id": chat.id,
                        "name": getattr(chat, 'title', 'Unknown'),
                        "username": f"@{chat.username}",
                        "participants": getattr(chat, 'participants_count', None),
                        "type": "channel" if getattr(chat, 'broadcast', False) else "group"
                    })
            return groups
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            me = await self.client.get_me()
            return {"id": me.id, "first_name": me.first_name, "username": me.username}
        except:
            return None
