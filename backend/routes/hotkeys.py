"""
Global Hotkeys WebSocket Route
Broadcasts global hotkey events to connected browser clients
"""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.global_hotkeys import (
    hotkey_manager, 
    get_pending_events,
    HOTKEY_CONFIG,
    init_global_hotkeys,
    start_hotkey_listener,
)

router = APIRouter(prefix="/hotkeys", tags=["hotkeys"])

# Flag to ensure we only start the listener once
_listener_started = False


@router.get("/config")
async def get_hotkey_config():
    """Get current hotkey configuration"""
    return {
        "hotkeys": HOTKEY_CONFIG,
        "status": "active"
    }


@router.websocket("/ws")
async def hotkey_websocket(websocket: WebSocket):
    """WebSocket endpoint for receiving global hotkey events"""
    global _listener_started
    
    # Start the global hotkey listener on first connection
    if not _listener_started:
        print("🎹 Starting global hotkey listener on first WebSocket connection...")
        try:
            start_hotkey_listener()
            _listener_started = True
            print("🎹 Global hotkey listener started successfully!")
        except Exception as e:
            print(f"❌ Failed to start hotkey listener: {e}")
            import traceback
            traceback.print_exc()
    
    await hotkey_manager.connect(websocket)
    
    try:
        while True:
            # Check for pending hotkey events
            events = get_pending_events()
            for event in events:
                try:
                    await websocket.send_json(event)
                except Exception as e:
                    print(f"Failed to send hotkey event: {e}")
                    break
            
            # Send keepalive periodically
            try:
                await websocket.send_json({'type': 'keepalive'})
            except Exception:
                break
            
            # Small delay to prevent busy loop
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Hotkey WebSocket error: {e}")
    finally:
        hotkey_manager.disconnect(websocket)


@router.post("/trigger/{action}")
async def trigger_action(action: str):
    """Manually trigger a hotkey action (for testing)"""
    import time
    
    event = {
        'type': 'hotkey',
        'key': 'manual',
        'action': action,
        'timestamp': time.time()
    }
    
    await hotkey_manager.broadcast(event)
    
    return {"status": "triggered", "action": action}
