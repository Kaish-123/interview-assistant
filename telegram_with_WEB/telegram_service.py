#!/usr/bin/env python3
"""
Telegram Service Layer
Handles all Telegram API interactions using Telethon
"""

import logging
from typing import Optional, Dict, Any, List
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, 
    ChatWriteForbiddenError,
    ChannelPrivateError,
    UserBannedInChannelError,
    ChatAdminRequiredError,
    SessionPasswordNeededError
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
        """Connect to Telegram"""
        try:
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            await self.client.connect()
            self.is_connected = True
            logger.info("Connected to Telegram")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            raise
    
    async def ensure_connected(self):
        """Ensure client is connected, reconnect if needed"""
        if not self.client:
            await self.connect()
            return
        
        try:
            # Check if actually connected
            if not self.client.is_connected():
                logger.info("Client disconnected, reconnecting...")
                await self.client.connect()
                self.is_connected = True
                logger.info("Reconnected successfully")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            # Try full reconnect
            try:
                self.client = TelegramClient(
                    self.session_name,
                    self.api_id,
                    self.api_hash
                )
                await self.client.connect()
                self.is_connected = True
                logger.info("Full reconnect successful")
            except Exception as e2:
                logger.error(f"Full reconnect failed: {e2}")
                self.is_connected = False
                raise
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            logger.info("Disconnected from Telegram")
    
    async def is_authorized(self) -> bool:
        """Check if user is authorized"""
        if not self.client:
            return False
        return await self.client.is_user_authorized()
    
    async def send_code(self, phone: str) -> str:
        """Send verification code to phone"""
        if not self.client:
            raise Exception("Not connected")
        
        result = await self.client.send_code_request(phone)
        self.phone_code_hash = result.phone_code_hash
        logger.info(f"Code sent to {phone}")
        return result.phone_code_hash
    
    async def sign_in(self, phone: str, code: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Sign in with verification code"""
        if not self.client:
            raise Exception("Not connected")
        
        try:
            if password:
                user = await self.client.sign_in(password=password)
            else:
                user = await self.client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=self.phone_code_hash
                )
            
            logger.info(f"Signed in as {user.first_name}")
            return {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "phone": user.phone
            }
        except SessionPasswordNeededError:
            raise Exception("Two-factor authentication required. Please provide password.")
        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            raise
    
    async def get_dialogs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user's dialogs (groups, channels, chats)"""
        if not self.client:
            raise Exception("Not connected")
        
        dialogs = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            entity = dialog.entity
            
            dialog_type = "unknown"
            if isinstance(entity, Channel):
                dialog_type = "channel" if entity.broadcast else "supergroup"
            elif isinstance(entity, Chat):
                dialog_type = "group"
            elif isinstance(entity, User):
                dialog_type = "user"
            
            # Get username
            username = None
            if hasattr(entity, 'username') and entity.username:
                username = f"@{entity.username}"
            
            dialogs.append({
                "id": dialog.id,
                "name": dialog.name,
                "username": username,
                "type": dialog_type,
                "unread_count": dialog.unread_count,
                "participants_count": getattr(entity, 'participants_count', None)
            })
        
        return dialogs
    
    async def send_message(self, target: str, message: str) -> Dict[str, Any]:
        """Send message to a target (group/channel/user)"""
        if not self.client:
            return {"success": False, "error": "Not connected"}
        
        # Auto-reconnect before sending
        try:
            await self.ensure_connected()
        except Exception as e:
            logger.error(f"Failed to ensure connection: {e}")
            return {"success": False, "error": f"Connection failed: {e}"}
        
        try:
            # Clean up target
            if not target.startswith("@"):
                target = f"@{target}"
            
            entity = await self.client.get_entity(target)
            await self.client.send_message(entity, message)
            
            logger.info(f"Message sent to {target}")
            return {"success": True, "target": target}
        
        except FloodWaitError as e:
            logger.warning(f"Flood wait: {e.seconds} seconds")
            return {"success": False, "error": f"Rate limited. Wait {e.seconds} seconds"}
        
        except ChatWriteForbiddenError:
            logger.warning(f"Cannot write to {target}")
            return {"success": False, "error": "Cannot write to this chat"}
        
        except ChannelPrivateError:
            logger.warning(f"Channel {target} is private")
            return {"success": False, "error": "Channel is private"}
        
        except UserBannedInChannelError:
            logger.warning(f"Banned from {target}")
            return {"success": False, "error": "Banned from this channel"}
        
        except ChatAdminRequiredError:
            logger.warning(f"Admin required for {target}")
            return {"success": False, "error": "Admin privileges required"}
        
        except ConnectionError as e:
            # Try one more time after reconnect
            logger.warning(f"Connection error, retrying: {e}")
            try:
                await self.ensure_connected()
                entity = await self.client.get_entity(target)
                await self.client.send_message(entity, message)
                logger.info(f"Message sent to {target} (after retry)")
                return {"success": True, "target": target}
            except Exception as retry_e:
                logger.error(f"Retry failed for {target}: {retry_e}")
                return {"success": False, "error": str(retry_e)}
        
        except Exception as e:
            error_str = str(e).lower()
            # Handle disconnection errors
            if "disconnect" in error_str or "connection" in error_str:
                logger.warning(f"Connection lost, retrying: {e}")
                try:
                    await self.ensure_connected()
                    entity = await self.client.get_entity(target)
                    await self.client.send_message(entity, message)
                    logger.info(f"Message sent to {target} (after reconnect)")
                    return {"success": True, "target": target}
                except Exception as retry_e:
                    logger.error(f"Reconnect retry failed for {target}: {retry_e}")
                    return {"success": False, "error": str(retry_e)}
            
            logger.error(f"Failed to send to {target}: {e}")
            return {"success": False, "error": str(e)}
    
    async def join_group(self, username: str) -> Dict[str, Any]:
        """Join a group or channel"""
        if not self.client:
            return {"success": False, "error": "Not connected"}
        
        try:
            if not username.startswith("@"):
                username = f"@{username}"
            
            entity = await self.client.get_entity(username)
            await self.client(JoinChannelRequest(entity))
            
            logger.info(f"Joined {username}")
            return {"success": True, "username": username}
        
        except Exception as e:
            logger.error(f"Failed to join {username}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Get current user info"""
        if not self.client:
            return None
        
        try:
            me = await self.client.get_me()
            return {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone
            }
        except:
            return None
    
    async def search_public(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for public groups/channels"""
        if not self.client:
            return []
        
        # Ensure connected before search
        try:
            await self.ensure_connected()
        except:
            pass
        
        try:
            from telethon.tl.functions.contacts import SearchRequest
            
            result = await self.client(SearchRequest(
                q=query,
                limit=limit
            ))
            
            groups = []
            for chat in result.chats:
                # Only include groups and channels (not users)
                if hasattr(chat, 'username') or hasattr(chat, 'megagroup'):
                    username = getattr(chat, 'username', None)
                    participants = getattr(chat, 'participants_count', None)
                    
                    groups.append({
                        "id": chat.id,
                        "name": getattr(chat, 'title', 'Unknown'),
                        "username": f"@{username}" if username else None,
                        "participants": participants,
                        "type": "channel" if getattr(chat, 'broadcast', False) else "group",
                        "verified": getattr(chat, 'verified', False)
                    })
            
            # Filter out entries without username (can't be joined easily)
            groups = [g for g in groups if g["username"]]
            
            logger.info(f"Search '{query}' found {len(groups)} groups")
            return groups
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


    async def check_can_post(self, username: str) -> Dict[str, Any]:
        """Check if we can post to a group/channel"""
        if not self.client:
            return {"can_post": False, "error": "Not connected"}
        
        try:
            await self.ensure_connected()
            
            if not username.startswith("@"):
                username = f"@{username}"
            
            entity = await self.client.get_entity(username)
            
            # Check entity type and permissions
            if hasattr(entity, 'broadcast') and entity.broadcast:
                # It's a channel - check if we're admin
                if hasattr(entity, 'admin_rights') and entity.admin_rights:
                    if entity.admin_rights.post_messages:
                        return {"can_post": True, "type": "channel", "name": getattr(entity, 'title', username)}
                return {"can_post": False, "error": "Channel - no post rights", "type": "channel"}
            
            # It's a group/supergroup
            if hasattr(entity, 'default_banned_rights'):
                banned = entity.default_banned_rights
                if banned and banned.send_messages:
                    return {"can_post": False, "error": "Sending messages restricted", "type": "group"}
            
            # Check if we're banned or restricted
            if hasattr(entity, 'left') and entity.left:
                return {"can_post": False, "error": "Left or kicked from group", "type": "group"}
            
            if hasattr(entity, 'restricted') and entity.restricted:
                return {"can_post": False, "error": "Restricted", "type": "group"}
            
            return {"can_post": True, "type": "group", "name": getattr(entity, 'title', username)}
            
        except ChannelPrivateError:
            return {"can_post": False, "error": "Private channel/group"}
        except Exception as e:
            error_str = str(e).lower()
            if "private" in error_str:
                return {"can_post": False, "error": "Private"}
            if "not found" in error_str or "no user" in error_str:
                return {"can_post": False, "error": "Not found"}
            return {"can_post": False, "error": str(e)}

    async def join_and_verify(self, username: str) -> Dict[str, Any]:
        """Join a group and verify if we can post"""
        if not self.client:
            return {"success": False, "error": "Not connected", "can_post": False}
        
        try:
            await self.ensure_connected()
            
            if not username.startswith("@"):
                username = f"@{username}"
            
            entity = await self.client.get_entity(username)
            
            # Try to join first
            try:
                await self.client(JoinChannelRequest(entity))
                logger.info(f"Joined {username}")
            except Exception as join_e:
                # Maybe already joined, continue to check
                logger.warning(f"Join attempt for {username}: {join_e}")
            
            # Now verify if we can post
            check = await self.check_can_post(username)
            
            if check.get("can_post"):
                return {
                    "success": True, 
                    "can_post": True, 
                    "username": username,
                    "name": check.get("name", username),
                    "type": check.get("type", "group")
                }
            else:
                # Can't post - leave the group
                try:
                    from telethon.tl.functions.channels import LeaveChannelRequest
                    await self.client(LeaveChannelRequest(entity))
                    logger.info(f"Left {username} - cannot post: {check.get('error')}")
                except:
                    pass
                return {
                    "success": False, 
                    "can_post": False, 
                    "error": check.get("error", "Cannot post"),
                    "username": username
                }
                
        except FloodWaitError as e:
            return {"success": False, "error": f"Rate limited ({e.seconds}s)", "can_post": False}
        except ChannelPrivateError:
            return {"success": False, "error": "Private channel", "can_post": False}
        except Exception as e:
            logger.error(f"Join and verify failed for {username}: {e}")
            return {"success": False, "error": str(e), "can_post": False}

# Import for join functionality
try:
    from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
except ImportError:
    pass

