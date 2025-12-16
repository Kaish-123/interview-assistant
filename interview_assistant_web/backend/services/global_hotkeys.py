"""
Global Hotkey Service for Interview Assistant
Uses a subprocess with proper macOS event loop for TRUE global keyboard capture
Works even when browser is not focused
"""
import threading
import subprocess
import time
import queue
import json
import os
from typing import Set, Dict, Any, List

# Thread-safe queue for cross-thread communication
_event_queue: queue.Queue = queue.Queue()
_listener_thread = None
_helper_process = None
_running = False

# Events file path
EVENTS_FILE = "/tmp/ia_hotkey_events.json"

# Hotkey configuration
HOTKEY_CONFIG = {
    'backtick': {
        'action': 'toggle_recording',
        'description': 'Start/Stop recording'
    },
    'page_down': {
        'action': 'scroll_bottom',
        'description': 'Scroll to bottom of chat'
    },
    'page_up': {
        'action': 'scroll_top', 
        'description': 'Scroll to top of chat'
    },
    'f2': {
        'action': 'save_layout',
        'description': 'Save current UI layout'
    },
    'escape': {
        'action': 'cancel_action',
        'description': 'Cancel current action'
    }
}


def start_hotkey_listener():
    """Start the global hotkey listener"""
    global _listener_thread, _helper_process, _running
    
    if _running:
        print("🎹 Global hotkey listener already running", flush=True)
        return
    
    _running = True
    
    # Start helper process
    helper_path = os.path.join(os.path.dirname(__file__), "hotkey_helper.py")
    try:
        _helper_process = subprocess.Popen(
            ["python3", helper_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"🎹 Started hotkey helper process (PID: {_helper_process.pid})", flush=True)
    except Exception as e:
        print(f"❌ Failed to start helper: {e}", flush=True)
    
    # Start file watcher thread
    _listener_thread = threading.Thread(target=_watch_events_file, daemon=True)
    _listener_thread.start()
    
    # Start output reader thread
    if _helper_process:
        output_thread = threading.Thread(target=_read_helper_output, daemon=True)
        output_thread.start()
    
    print("🎹 Global hotkey listener started", flush=True)


def stop_hotkey_listener():
    """Stop the global hotkey listener"""
    global _running, _helper_process
    _running = False
    
    if _helper_process:
        try:
            _helper_process.terminate()
            _helper_process.wait(timeout=2)
        except:
            try:
                _helper_process.kill()
            except:
                pass
        _helper_process = None
    
    print("🎹 Global hotkey listener stopped", flush=True)


def _read_helper_output():
    """Read and print output from helper process"""
    global _helper_process
    import sys
    
    if not _helper_process:
        return
    
    try:
        for line in _helper_process.stdout:
            if not _running:
                break
            sys.stderr.write(f"[Helper] {line}")
            sys.stderr.flush()
    except:
        pass


def _watch_events_file():
    """Watch the events file for new hotkey events"""
    global _running
    
    import sys
    last_timestamp = 0
    last_mtime = 0
    
    # Clear any old events
    try:
        os.remove(EVENTS_FILE)
    except:
        pass
    
    sys.stderr.write("🎹 Watching for global hotkey events...\n")
    sys.stderr.flush()
    
    while _running:
        try:
            if os.path.exists(EVENTS_FILE):
                # Check if file was modified
                mtime = os.path.getmtime(EVENTS_FILE)
                if mtime > last_mtime:
                    last_mtime = mtime
                    
                    # Read event
                    with open(EVENTS_FILE, 'r') as f:
                        event = json.load(f)
                    
                    # Check if it's a new event
                    if event.get('timestamp', 0) > last_timestamp:
                        last_timestamp = event['timestamp']
                        
                        # Queue the event
                        _event_queue.put(event)
                        sys.stderr.write(f"🎹 Received global hotkey: {event.get('key')} -> {event.get('action')}\n")
                        sys.stderr.flush()
            
            time.sleep(0.05)  # 50ms polling
            
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Watch error: {e}\n")
            sys.stderr.flush()
            time.sleep(0.1)


def get_pending_events() -> List[Dict[str, Any]]:
    """Get all pending hotkey events (non-blocking)"""
    events = []
    while True:
        try:
            event = _event_queue.get_nowait()
            events.append(event)
        except queue.Empty:
            break
    return events


class HotkeyConnectionManager:
    def __init__(self):
        self.active_connections: Set = set()
    
    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"🔌 Hotkey client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket):
        self.active_connections.discard(websocket)
        print(f"🔌 Hotkey client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        for conn in disconnected:
            self.active_connections.discard(conn)


hotkey_manager = HotkeyConnectionManager()


def init_global_hotkeys():
    """Initialize global hotkey system"""
    start_hotkey_listener()
