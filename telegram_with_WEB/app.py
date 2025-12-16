#!/usr/bin/env python3
"""
TechyEra Telegram Marketing - Web Dashboard
Professional web-based Telegram marketing automation tool
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from telegram_service import TelegramService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables
telegram_service: Optional[TelegramService] = None
scheduler: Optional[AsyncIOScheduler] = None
activity_log: List[dict] = []
stats = {
    "messages_sent_today": 0,
    "groups_reached_today": 0,
    "last_send_time": None,
    "next_send_time": None,
    "total_messages_sent": 0,
    "errors_today": 0
}

CONFIG_FILE = "config.json"

# Pydantic Models
class ConfigUpdate(BaseModel):
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    phone_number: Optional[str] = None

class SettingsUpdate(BaseModel):
    auto_send_enabled: Optional[bool] = None
    send_interval_minutes: Optional[int] = None
    delay_between_groups_seconds: Optional[int] = None
    auto_growth_enabled: Optional[bool] = None
    growth_interval_hours: Optional[int] = None
    max_groups_per_growth: Optional[int] = None

class GroupAdd(BaseModel):
    username: str
    name: Optional[str] = None
    enabled: bool = True

class MessageAdd(BaseModel):
    text: str
    enabled: bool = True

class LoginCode(BaseModel):
    code: str

class PhoneCodeRequest(BaseModel):
    phone_number: str

class SearchQuery(BaseModel):
    query: str
    limit: int = 20

class BulkGroupAdd(BaseModel):
    groups: List[dict]

class KeywordsUpdate(BaseModel):
    keywords: List[str]

# Helper functions
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "api_id": "",
            "api_hash": "",
            "phone_number": "",
            "session_name": "web_marketing_session",
            "settings": {
                "auto_send_enabled": False,
                "send_interval_minutes": 30,
                "delay_between_groups_seconds": 3,
                "auto_growth_enabled": False,
                "growth_interval_hours": 6,
                "max_groups_per_growth": 5,
                "growth_keywords": [
                    "proxy interview",
                    "job support",
                    "data engineer jobs",
                    "developer jobs",
                    "IT jobs USA",
                    "fullstack developer"
                ]
            },
            "targets": [],
            "messages": []
        }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def add_activity(action: str, details: str, status: str = "success"):
    global activity_log
    activity_log.insert(0, {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
        "status": status
    })
    # Keep only last 100 activities
    activity_log = activity_log[:100]

async def send_messages_task():
    """Background task to send messages to all groups"""
    global stats, telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        logger.warning("Telegram not connected, skipping send")
        return
    
    config = load_config()
    enabled_targets = [t for t in config.get("targets", []) if t.get("enabled", True)]
    enabled_messages = [m for m in config.get("messages", []) if m.get("enabled", True)]
    
    if not enabled_targets or not enabled_messages:
        logger.warning("No targets or messages configured")
        return
    
    delay = config.get("settings", {}).get("delay_between_groups_seconds", 3)
    message = enabled_messages[0]["text"]
    
    success_count = 0
    error_count = 0
    
    for target in enabled_targets:
        try:
            result = await telegram_service.send_message(target["username"], message)
            if result["success"]:
                success_count += 1
                add_activity("Message Sent", f"Sent to {target.get('name', target['username'])}")
            else:
                error_count += 1
                add_activity("Send Failed", f"Failed: {target.get('name', target['username'])} - {result.get('error', 'Unknown')}", "error")
            await asyncio.sleep(delay)
        except Exception as e:
            error_count += 1
            add_activity("Error", f"Error sending to {target['username']}: {str(e)}", "error")
    
    stats["messages_sent_today"] += success_count
    stats["groups_reached_today"] = success_count
    stats["total_messages_sent"] += success_count
    stats["errors_today"] += error_count
    stats["last_send_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate next send time
    interval = config.get("settings", {}).get("send_interval_minutes", 30)
    stats["next_send_time"] = (datetime.now() + timedelta(minutes=interval)).strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"Batch complete: {success_count} sent, {error_count} failed")

def setup_scheduler():
    """Setup the scheduler for auto-send"""
    global scheduler
    
    config = load_config()
    settings = config.get("settings", {})
    
    if scheduler:
        scheduler.shutdown(wait=False)
    
    scheduler = AsyncIOScheduler()
    
    if settings.get("auto_send_enabled", False):
        interval = settings.get("send_interval_minutes", 30)
        scheduler.add_job(
            send_messages_task,
            IntervalTrigger(minutes=interval),
            id="auto_send",
            name="Auto Send Messages",
            replace_existing=True
        )
        stats["next_send_time"] = (datetime.now() + timedelta(minutes=interval)).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Auto-send enabled: every {interval} minutes")
    
    scheduler.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global telegram_service
    
    # Startup
    logger.info("Starting TechyEra Telegram Marketing Web Dashboard...")
    config = load_config()
    
    if config.get("api_id") and config.get("api_hash"):
        telegram_service = TelegramService(
            api_id=int(config["api_id"]),
            api_hash=config["api_hash"],
            session_name=config.get("session_name", "web_marketing_session")
        )
        try:
            await telegram_service.connect()
            if await telegram_service.is_authorized():
                logger.info("Telegram connected and authorized!")
                add_activity("System", "Telegram connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect Telegram: {e}")
    
    setup_scheduler()
    
    yield
    
    # Shutdown
    if scheduler:
        scheduler.shutdown(wait=False)
    if telegram_service:
        await telegram_service.disconnect()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="TechyEra Telegram Marketing",
    description="Professional Telegram Marketing Automation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ==================== API ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/status")
async def get_status():
    """Get overall system status"""
    global telegram_service, stats
    
    config = load_config()
    is_connected = telegram_service and telegram_service.is_connected
    is_authorized = False
    
    if is_connected:
        try:
            is_authorized = await telegram_service.is_authorized()
        except:
            pass
    
    return {
        "telegram_connected": is_connected,
        "telegram_authorized": is_authorized,
        "auto_send_enabled": config.get("settings", {}).get("auto_send_enabled", False),
        "auto_growth_enabled": config.get("settings", {}).get("auto_growth_enabled", False),
        "total_groups": len(config.get("targets", [])),
        "enabled_groups": len([t for t in config.get("targets", []) if t.get("enabled", True)]),
        "stats": stats
    }

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    config = load_config()
    # Mask sensitive data
    return {
        "api_id": config.get("api_id", "")[:4] + "****" if config.get("api_id") else "",
        "api_hash": config.get("api_hash", "")[:8] + "****" if config.get("api_hash") else "",
        "phone_number": config.get("phone_number", ""),
        "settings": config.get("settings", {}),
        "has_credentials": bool(config.get("api_id") and config.get("api_hash"))
    }

@app.post("/api/config")
async def update_config(config_update: ConfigUpdate):
    """Update API credentials"""
    config = load_config()
    
    if config_update.api_id:
        config["api_id"] = config_update.api_id
    if config_update.api_hash:
        config["api_hash"] = config_update.api_hash
    if config_update.phone_number:
        config["phone_number"] = config_update.phone_number
    
    save_config(config)
    add_activity("Config", "API credentials updated")
    
    return {"success": True, "message": "Configuration updated"}

@app.get("/api/settings")
async def get_settings():
    """Get automation settings"""
    config = load_config()
    return config.get("settings", {})

@app.post("/api/settings")
async def update_settings(settings_update: SettingsUpdate):
    """Update automation settings"""
    config = load_config()
    settings = config.get("settings", {})
    
    update_dict = settings_update.model_dump(exclude_none=True)
    settings.update(update_dict)
    config["settings"] = settings
    
    save_config(config)
    setup_scheduler()  # Restart scheduler with new settings
    
    add_activity("Settings", f"Settings updated: {list(update_dict.keys())}")
    
    return {"success": True, "settings": settings}

@app.get("/api/groups")
async def get_groups():
    """Get all target groups"""
    config = load_config()
    return config.get("targets", [])

@app.post("/api/groups")
async def add_group(group: GroupAdd):
    """Add a new target group"""
    config = load_config()
    
    # Check if already exists
    existing = [t for t in config.get("targets", []) if t.get("username") == group.username]
    if existing:
        raise HTTPException(status_code=400, detail="Group already exists")
    
    new_group = {
        "name": group.name or group.username,
        "username": group.username if group.username.startswith("@") else f"@{group.username}",
        "enabled": group.enabled,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    config.setdefault("targets", []).append(new_group)
    save_config(config)
    
    add_activity("Group Added", f"Added {new_group['username']}")
    
    return {"success": True, "group": new_group}

@app.delete("/api/groups/{username}")
async def delete_group(username: str):
    """Delete a target group"""
    config = load_config()
    
    original_count = len(config.get("targets", []))
    config["targets"] = [t for t in config.get("targets", []) if t.get("username") != username and t.get("username") != f"@{username}"]
    
    if len(config["targets"]) == original_count:
        raise HTTPException(status_code=404, detail="Group not found")
    
    save_config(config)
    add_activity("Group Removed", f"Removed {username}")
    
    return {"success": True}

@app.put("/api/groups/{username}/toggle")
async def toggle_group(username: str):
    """Toggle group enabled/disabled"""
    config = load_config()
    
    for target in config.get("targets", []):
        if target.get("username") == username or target.get("username") == f"@{username}":
            target["enabled"] = not target.get("enabled", True)
            save_config(config)
            add_activity("Group Toggled", f"{username} {'enabled' if target['enabled'] else 'disabled'}")
            return {"success": True, "enabled": target["enabled"]}
    
    raise HTTPException(status_code=404, detail="Group not found")

@app.get("/api/messages")
async def get_messages():
    """Get all marketing messages"""
    config = load_config()
    return config.get("messages", [])

@app.post("/api/messages")
async def add_message(message: MessageAdd):
    """Add a new marketing message"""
    config = load_config()
    
    new_message = {
        "id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "text": message.text,
        "enabled": message.enabled,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    config.setdefault("messages", []).append(new_message)
    save_config(config)
    
    add_activity("Message Added", f"New message added ({len(message.text)} chars)")
    
    return {"success": True, "message": new_message}

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: str):
    """Delete a marketing message"""
    config = load_config()
    
    original_count = len(config.get("messages", []))
    config["messages"] = [m for m in config.get("messages", []) if m.get("id") != message_id]
    
    if len(config["messages"]) == original_count:
        raise HTTPException(status_code=404, detail="Message not found")
    
    save_config(config)
    add_activity("Message Removed", f"Message {message_id} removed")
    
    return {"success": True}

@app.put("/api/messages/{message_id}/toggle")
async def toggle_message(message_id: str):
    """Toggle message enabled/disabled"""
    config = load_config()
    
    for msg in config.get("messages", []):
        if msg.get("id") == message_id:
            msg["enabled"] = not msg.get("enabled", True)
            save_config(config)
            return {"success": True, "enabled": msg["enabled"]}
    
    raise HTTPException(status_code=404, detail="Message not found")

@app.get("/api/activity")
async def get_activity():
    """Get recent activity log"""
    return activity_log[:50]

@app.post("/api/send/now")
async def send_now(background_tasks: BackgroundTasks):
    """Manually trigger message sending"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    if not await telegram_service.is_authorized():
        raise HTTPException(status_code=400, detail="Telegram not authorized")
    
    background_tasks.add_task(send_messages_task)
    add_activity("Manual Send", "Manual send triggered")
    
    return {"success": True, "message": "Sending started in background"}

@app.post("/api/send/single")
async def send_single(username: str, message: str):
    """Send a single message to a specific group"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    result = await telegram_service.send_message(username, message)
    
    if result["success"]:
        add_activity("Single Send", f"Sent to {username}")
        stats["total_messages_sent"] += 1
    else:
        add_activity("Send Failed", f"Failed to send to {username}: {result.get('error')}", "error")
    
    return result

# ==================== TELEGRAM AUTH ====================

@app.post("/api/telegram/connect")
async def connect_telegram():
    """Initialize Telegram connection"""
    global telegram_service
    
    config = load_config()
    
    if not config.get("api_id") or not config.get("api_hash"):
        raise HTTPException(status_code=400, detail="API credentials not configured")
    
    telegram_service = TelegramService(
        api_id=int(config["api_id"]),
        api_hash=config["api_hash"],
        session_name=config.get("session_name", "web_marketing_session")
    )
    
    try:
        await telegram_service.connect()
        is_auth = await telegram_service.is_authorized()
        add_activity("Telegram", "Connected to Telegram")
        return {"success": True, "authorized": is_auth}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram/request-code")
async def request_code(data: PhoneCodeRequest):
    """Request verification code"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    try:
        result = await telegram_service.send_code(data.phone_number)
        
        # Save phone number to config
        config = load_config()
        config["phone_number"] = data.phone_number
        save_config(config)
        
        add_activity("Auth", f"Code requested for {data.phone_number}")
        return {"success": True, "phone_code_hash": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram/verify-code")
async def verify_code(data: LoginCode):
    """Verify the login code"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    config = load_config()
    phone = config.get("phone_number")
    
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number not set")
    
    try:
        result = await telegram_service.sign_in(phone, data.code)
        add_activity("Auth", "Successfully logged in to Telegram")
        setup_scheduler()  # Start scheduler after successful auth
        return {"success": True, "user": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/telegram/dialogs")
async def get_dialogs():
    """Get list of user's Telegram dialogs (groups/channels)"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    try:
        dialogs = await telegram_service.get_dialogs()
        return {"success": True, "dialogs": dialogs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram/join/{username}")
async def join_group(username: str):
    """Join a group/channel"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    try:
        result = await telegram_service.join_group(username)
        if result["success"]:
            add_activity("Group Joined", f"Joined {username}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-send/start")
async def start_auto_send():
    """Start auto-send"""
    config = load_config()
    config["settings"]["auto_send_enabled"] = True
    save_config(config)
    setup_scheduler()
    add_activity("Auto-Send", "Auto-send started")
    return {"success": True, "message": "Auto-send started"}

@app.post("/api/auto-send/stop")
async def stop_auto_send():
    """Stop auto-send"""
    global scheduler
    
    config = load_config()
    config["settings"]["auto_send_enabled"] = False
    save_config(config)
    
    if scheduler:
        try:
            scheduler.remove_job("auto_send")
        except:
            pass
    
    stats["next_send_time"] = None
    add_activity("Auto-Send", "Auto-send stopped")
    return {"success": True, "message": "Auto-send stopped"}

@app.get("/api/stats/reset")
async def reset_stats():
    """Reset daily stats"""
    global stats
    stats["messages_sent_today"] = 0
    stats["groups_reached_today"] = 0
    stats["errors_today"] = 0
    add_activity("Stats", "Daily stats reset")
    return {"success": True}

# ==================== GROUP SEARCH & DISCOVERY ====================

@app.post("/api/telegram/search")
async def search_groups(data: SearchQuery):
    """Search for groups/channels on Telegram"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    try:
        results = await telegram_service.search_public(data.query, data.limit)
        return {"success": True, "results": results, "query": data.query}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/growth/keywords")
async def get_growth_keywords():
    """Get current growth keywords"""
    config = load_config()
    keywords = config.get("settings", {}).get("growth_keywords", [])
    return {"keywords": keywords}

@app.post("/api/growth/keywords")
async def update_growth_keywords(data: KeywordsUpdate):
    """Update growth keywords"""
    config = load_config()
    config.setdefault("settings", {})["growth_keywords"] = data.keywords
    save_config(config)
    add_activity("Keywords", f"Updated {len(data.keywords)} growth keywords")
    return {"success": True, "keywords": data.keywords}

@app.post("/api/growth/keywords/add")
async def add_growth_keyword(keyword: str):
    """Add a single growth keyword"""
    config = load_config()
    keywords = config.get("settings", {}).get("growth_keywords", [])
    if keyword not in keywords:
        keywords.append(keyword)
        config.setdefault("settings", {})["growth_keywords"] = keywords
        save_config(config)
        add_activity("Keyword Added", f"Added keyword: {keyword}")
    return {"success": True, "keywords": keywords}

@app.delete("/api/growth/keywords/{keyword}")
async def remove_growth_keyword(keyword: str):
    """Remove a growth keyword"""
    config = load_config()
    keywords = config.get("settings", {}).get("growth_keywords", [])
    if keyword in keywords:
        keywords.remove(keyword)
        config.setdefault("settings", {})["growth_keywords"] = keywords
        save_config(config)
        add_activity("Keyword Removed", f"Removed keyword: {keyword}")
    return {"success": True, "keywords": keywords}

@app.post("/api/groups/bulk")
async def bulk_add_groups(data: BulkGroupAdd):
    """Add multiple groups at once"""
    config = load_config()
    added = 0
    existing_usernames = [t.get("username") for t in config.get("targets", [])]
    
    for group in data.groups:
        username = group.get("username", "")
        if not username.startswith("@"):
            username = f"@{username}"
        
        if username not in existing_usernames:
            new_group = {
                "name": group.get("name", username),
                "username": username,
                "enabled": True,
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            config.setdefault("targets", []).append(new_group)
            existing_usernames.append(username)
            added += 1
    
    save_config(config)
    add_activity("Bulk Add", f"Added {added} new groups")
    return {"success": True, "added": added}

@app.post("/api/growth/discover")
async def discover_groups(data: SearchQuery):
    """Discover groups based on a keyword"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    try:
        results = await telegram_service.search_public(data.query, data.limit)
        
        # Filter out already added groups
        config = load_config()
        existing = [t.get("username", "").lower() for t in config.get("targets", [])]
        
        filtered = []
        for r in results:
            username = r.get("username", "")
            if username and username.lower() not in existing and f"@{username.lower()}" not in existing:
                filtered.append(r)
        
        return {
            "success": True, 
            "results": filtered, 
            "query": data.query,
            "total_found": len(results),
            "new_groups": len(filtered)
        }
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-growth/start")
async def start_auto_growth():
    """Start auto-growth"""
    config = load_config()
    config["settings"]["auto_growth_enabled"] = True
    save_config(config)
    setup_scheduler()
    add_activity("Auto-Growth", "Auto-growth started")
    return {"success": True, "message": "Auto-growth started"}

@app.post("/api/auto-growth/stop")
async def stop_auto_growth():
    """Stop auto-growth"""
    config = load_config()
    config["settings"]["auto_growth_enabled"] = False
    save_config(config)
    add_activity("Auto-Growth", "Auto-growth stopped")
    return {"success": True, "message": "Auto-growth stopped"}

@app.get("/api/growth/status")
async def get_growth_status():
    """Get auto-growth status"""
    config = load_config()
    settings = config.get("settings", {})
    return {
        "enabled": settings.get("auto_growth_enabled", False),
        "interval_hours": settings.get("growth_interval_hours", 6),
        "max_groups": settings.get("max_groups_per_growth", 5),
        "keywords": settings.get("growth_keywords", []),
        "total_targets": len(config.get("targets", []))
    }

@app.post("/api/growth/now")
async def grow_now():
    """Manually trigger growth - find and add postable groups only"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    if not await telegram_service.is_authorized():
        raise HTTPException(status_code=400, detail="Telegram not authorized")
    
    config = load_config()
    settings = config.get("settings", {})
    keywords = settings.get("growth_keywords", [])
    max_groups = settings.get("max_groups_per_growth", 5)
    
    if not keywords:
        raise HTTPException(status_code=400, detail="No growth keywords configured")
    
    added = 0
    skipped = 0
    checked = 0
    existing_usernames = [t.get("username", "").lower() for t in config.get("targets", [])]
    
    add_activity("Growth", f"Starting growth with {len(keywords)} keywords...")
    
    import random
    random.shuffle(keywords)  # Randomize keyword order
    
    for keyword in keywords[:3]:  # Use up to 3 keywords per run
        if added >= max_groups:
            break
            
        try:
            # Search for groups
            results = await telegram_service.search_public(keyword, limit=20)
            add_activity("Search", f"Found {len(results)} groups for '{keyword}'")
            
            for group in results:
                if added >= max_groups:
                    break
                    
                username = group.get("username", "")
                if not username:
                    continue
                    
                # Skip if already in list
                if username.lower() in existing_usernames or username.lower().lstrip("@") in existing_usernames:
                    continue
                
                checked += 1
                
                # Join and verify if we can post
                result = await telegram_service.join_and_verify(username)
                
                if result.get("success") and result.get("can_post"):
                    # Add to targets
                    new_group = {
                        "name": result.get("name", username),
                        "username": username if username.startswith("@") else f"@{username}",
                        "enabled": True,
                        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "source": f"growth:{keyword}"
                    }
                    config.setdefault("targets", []).append(new_group)
                    existing_usernames.append(username.lower())
                    added += 1
                    add_activity("Growth", f"✅ Added {new_group['name']} (can post)", "success")
                else:
                    skipped += 1
                    error = result.get("error", "Cannot post")
                    add_activity("Growth", f"⏭️ Skipped {username}: {error}", "warning")
                
                # Delay between checks to avoid rate limiting
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Growth error for keyword '{keyword}': {e}")
            add_activity("Growth Error", f"Error searching '{keyword}': {str(e)}", "error")
    
    save_config(config)
    
    add_activity("Growth Complete", f"Added {added} groups, skipped {skipped} (checked {checked})", "success")
    
    return {
        "success": True,
        "added": added,
        "skipped": skipped,
        "checked": checked,
        "total_groups": len(config.get("targets", []))
    }

@app.post("/api/groups/verify")
async def verify_groups():
    """Verify all existing groups and remove non-postable ones"""
    global telegram_service
    
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    config = load_config()
    targets = config.get("targets", [])
    
    verified = []
    removed = 0
    
    add_activity("Verify", f"Checking {len(targets)} groups...")
    
    for target in targets:
        username = target.get("username", "")
        if not username:
            continue
        
        try:
            result = await telegram_service.check_can_post(username)
            
            if result.get("can_post"):
                verified.append(target)
            else:
                removed += 1
                add_activity("Removed", f"❌ {target.get('name', username)}: {result.get('error')}", "warning")
            
            await asyncio.sleep(1)  # Delay between checks
            
        except Exception as e:
            # Keep if check fails (benefit of doubt)
            verified.append(target)
            logger.warning(f"Check failed for {username}: {e}")
    
    config["targets"] = verified
    save_config(config)
    
    add_activity("Verify Complete", f"Kept {len(verified)} groups, removed {removed}", "success")
    
    return {
        "success": True,
        "verified": len(verified),
        "removed": removed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)

