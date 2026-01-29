#!/usr/bin/env python3
"""TechyEra Telegram Marketing - Web Dashboard"""
import os, json, asyncio, logging
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

telegram_service: Optional[TelegramService] = None
scheduler: Optional[AsyncIOScheduler] = None
activity_log: List[dict] = []
stats = {"messages_sent_today": 0, "groups_reached_today": 0, "last_send_time": None,
         "next_send_time": None, "total_messages_sent": 0, "errors_today": 0}
CONFIG_FILE = "config.json"

class GroupAdd(BaseModel):
    username: str
    name: Optional[str] = None
    enabled: bool = True

class MessageAdd(BaseModel):
    text: str
    enabled: bool = True

class SettingsUpdate(BaseModel):
    auto_send_enabled: Optional[bool] = None
    send_interval_minutes: Optional[int] = None
    delay_between_groups_seconds: Optional[int] = None

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"api_id": "", "api_hash": "", "phone_number": "", "settings": {}, "targets": [], "messages": []}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def add_activity(action: str, details: str, status: str = "success"):
    global activity_log
    activity_log.insert(0, {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "action": action, "details": details, "status": status})
    activity_log = activity_log[:100]

async def send_messages_task():
    global stats, telegram_service
    if not telegram_service or not telegram_service.is_connected:
        logger.warning("Telegram not connected, skipping send")
        return
    config = load_config()
    enabled_targets = [t for t in config.get("targets", []) if t.get("enabled", True)]
    enabled_messages = [m for m in config.get("messages", []) if m.get("enabled", True)]
    if not enabled_targets or not enabled_messages:
        return
    delay = config.get("settings", {}).get("delay_between_groups_seconds", 3)
    message = enabled_messages[0]["text"]
    success_count, error_count = 0, 0
    for target in enabled_targets:
        try:
            result = await telegram_service.send_message(target["username"], message)
            if result["success"]:
                success_count += 1
                add_activity("Message Sent", f"Sent to {target.get('name', target['username'])}")
            else:
                error_count += 1
                add_activity("Send Failed", f"Failed: {target.get('name', target['username'])} - {result.get('error')}", "error")
            await asyncio.sleep(delay)
        except Exception as e:
            error_count += 1
            add_activity("Error", f"Error: {target['username']}: {str(e)}", "error")
    stats["messages_sent_today"] += success_count
    stats["groups_reached_today"] = success_count
    stats["total_messages_sent"] += success_count
    stats["errors_today"] += error_count
    stats["last_send_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    interval = config.get("settings", {}).get("send_interval_minutes", 30)
    stats["next_send_time"] = (datetime.now() + timedelta(minutes=interval)).strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Batch complete: {success_count} sent, {error_count} failed")

def setup_scheduler():
    global scheduler
    config = load_config()
    settings = config.get("settings", {})
    if scheduler:
        scheduler.shutdown(wait=False)
    scheduler = AsyncIOScheduler()
    if settings.get("auto_send_enabled", False):
        interval = settings.get("send_interval_minutes", 30)
        scheduler.add_job(send_messages_task, IntervalTrigger(minutes=interval), id="auto_send", replace_existing=True)
        stats["next_send_time"] = (datetime.now() + timedelta(minutes=interval)).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Auto-send enabled: every {interval} minutes")
    scheduler.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_service
    logger.info("Starting TechyEra Telegram Marketing Web Dashboard...")
    config = load_config()
    if config.get("api_id") and config.get("api_hash"):
        telegram_service = TelegramService(int(config["api_id"]), config["api_hash"], config.get("session_name", "web_marketing_session"))
        try:
            await telegram_service.connect()
            if await telegram_service.is_authorized():
                logger.info("Telegram connected and authorized!")
                add_activity("System", "Telegram connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect Telegram: {e}")
    setup_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)
    if telegram_service:
        await telegram_service.disconnect()

app = FastAPI(title="TechyEra Telegram Marketing", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/status")
async def get_status():
    config = load_config()
    is_connected = telegram_service and telegram_service.is_connected
    is_authorized = False
    if is_connected:
        try:
            is_authorized = await telegram_service.is_authorized()
        except:
            pass
    return {"telegram_connected": is_connected, "telegram_authorized": is_authorized,
            "auto_send_enabled": config.get("settings", {}).get("auto_send_enabled", False),
            "total_groups": len(config.get("targets", [])),
            "enabled_groups": len([t for t in config.get("targets", []) if t.get("enabled", True)]),
            "stats": stats}

@app.get("/api/groups")
async def get_groups():
    return load_config().get("targets", [])

@app.post("/api/groups")
async def add_group(group: GroupAdd):
    config = load_config()
    new_group = {"name": group.name or group.username, 
                 "username": group.username if group.username.startswith("@") else f"@{group.username}",
                 "enabled": group.enabled, "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    config.setdefault("targets", []).append(new_group)
    save_config(config)
    add_activity("Group Added", f"Added {new_group['username']}")
    return {"success": True, "group": new_group}

@app.delete("/api/groups/{username}")
async def delete_group(username: str):
    config = load_config()
    config["targets"] = [t for t in config.get("targets", []) if t.get("username") != username and t.get("username") != f"@{username}"]
    save_config(config)
    return {"success": True}

@app.put("/api/groups/{username}/toggle")
async def toggle_group(username: str):
    config = load_config()
    for target in config.get("targets", []):
        if target.get("username") == username or target.get("username") == f"@{username}":
            target["enabled"] = not target.get("enabled", True)
            save_config(config)
            return {"success": True, "enabled": target["enabled"]}
    raise HTTPException(status_code=404, detail="Group not found")

@app.get("/api/messages")
async def get_messages():
    return load_config().get("messages", [])

@app.post("/api/messages")
async def add_message(message: MessageAdd):
    config = load_config()
    new_message = {"id": f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}", "text": message.text,
                   "enabled": message.enabled, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    config.setdefault("messages", []).append(new_message)
    save_config(config)
    return {"success": True, "message": new_message}

@app.get("/api/activity")
async def get_activity():
    return activity_log[:50]

@app.post("/api/send/now")
async def send_now(background_tasks: BackgroundTasks):
    if not telegram_service or not telegram_service.is_connected:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    background_tasks.add_task(send_messages_task)
    add_activity("Manual Send", "Manual send triggered")
    return {"success": True, "message": "Sending started"}

@app.post("/api/auto-send/start")
async def start_auto_send():
    config = load_config()
    config["settings"]["auto_send_enabled"] = True
    save_config(config)
    setup_scheduler()
    return {"success": True}

@app.post("/api/auto-send/stop")
async def stop_auto_send():
    config = load_config()
    config["settings"]["auto_send_enabled"] = False
    save_config(config)
    if scheduler:
        try:
            scheduler.remove_job("auto_send")
        except:
            pass
    stats["next_send_time"] = None
    return {"success": True}

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    config = load_config()
    if settings.auto_send_enabled is not None:
        config["settings"]["auto_send_enabled"] = settings.auto_send_enabled
    if settings.send_interval_minutes is not None:
        config["settings"]["send_interval_minutes"] = settings.send_interval_minutes
    if settings.delay_between_groups_seconds is not None:
        config["settings"]["delay_between_groups_seconds"] = settings.delay_between_groups_seconds
    save_config(config)
    setup_scheduler()
    return {"success": True}

@app.get("/api/settings")
async def get_settings():
    return load_config().get("settings", {})

@app.get("/api/config")
async def get_config():
    config = load_config()
    return {"api_id": config.get("api_id", "")[:4] + "****" if config.get("api_id") else "",
            "phone_number": config.get("phone_number", ""), "settings": config.get("settings", {})}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
