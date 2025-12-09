#!/usr/bin/env python3
"""
Global Hotkey Listener for Interview Assistant Web

This script runs alongside the web app and captures global hotkeys even when
the browser is not focused. It sends commands to the backend via HTTP/WebSocket.

Usage:
    python global_hotkeys.py

Requirements:
    pip install pynput requests websocket-client

Hotkeys:
    ` (backtick)     - Toggle recording
    ~ (tilde)        - Force stop recording
    1 + 2            - Focus chat input (brings browser to front)
    2 + 3            - Upload resume
    3 + 4            - Toggle fast mode
    4 + 5            - Record with BlackHole (internal)
    5 + 6            - Record with Microphone (external)
    Cmd + N          - New chat
    Cmd + Shift + S  - Quick setup
    F6               - Quick setup
    F8               - New chat
"""

import os
import sys
import json
import time
import threading
import subprocess
from typing import Set, Optional

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
except ImportError:
    print("❌ pynput not installed. Run: pip install pynput")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import websocket
except ImportError:
    print("⚠️ websocket-client not installed. Some features may not work.")
    print("   Run: pip install websocket-client")
    websocket = None

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
WS_URL = "ws://localhost:8000/chat/ws"

# State
current_keys: Set = set()
is_recording = False
current_session_id: Optional[int] = None
ws_connection = None

# ============================================================================
# Helper Functions
# ============================================================================

def bring_browser_to_front():
    """Bring Chrome/browser window to front (macOS)"""
    try:
        script = '''
        tell application "Google Chrome"
            activate
            set index of first window to 1
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
        print("🌐 Brought browser to front")
    except Exception as e:
        print(f"⚠️ Could not bring browser to front: {e}")

def send_backend_command(endpoint: str, method: str = "POST", data: dict = None):
    """Send command to backend API"""
    try:
        url = f"{BACKEND_URL}/{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=2)
        else:
            response = requests.post(url, json=data or {}, timeout=2)
        return response.json() if response.ok else None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Backend request failed: {e}")
        return None

def get_current_session():
    """Get the most recent session ID"""
    global current_session_id
    try:
        response = requests.get(f"{BACKEND_URL}/chat/sessions", timeout=2)
        if response.ok:
            sessions = response.json()
            if sessions:
                current_session_id = sessions[0]["id"]
                return current_session_id
    except:
        pass
    return None

def send_ws_message(action: str, **kwargs):
    """Send message via WebSocket"""
    global ws_connection, current_session_id
    
    if not websocket:
        print("⚠️ WebSocket not available")
        return
    
    if not current_session_id:
        get_current_session()
    
    if not current_session_id:
        print("⚠️ No active session")
        return
    
    try:
        if not ws_connection or not ws_connection.connected:
            ws_connection = websocket.create_connection(
                f"{WS_URL}/{current_session_id}",
                timeout=2
            )
        
        message = {"action": action, **kwargs}
        ws_connection.send(json.dumps(message))
        print(f"📤 Sent: {action}")
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        ws_connection = None

# ============================================================================
# Hotkey Actions
# ============================================================================

def action_toggle_recording():
    """Toggle recording (backtick key)"""
    global is_recording
    bring_browser_to_front()
    
    # Simulate backtick key press in browser
    # We'll use AppleScript to send key to Chrome
    try:
        script = '''
        tell application "System Events"
            tell process "Google Chrome"
                key code 50
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
        is_recording = not is_recording
        status = "🎤 Recording started" if is_recording else "🛑 Recording stopped"
        print(status)
    except Exception as e:
        print(f"⚠️ Toggle recording failed: {e}")

def action_force_stop():
    """Force stop recording (tilde key)"""
    global is_recording
    bring_browser_to_front()
    
    try:
        script = '''
        tell application "System Events"
            tell process "Google Chrome"
                key code 50 using shift down
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
        is_recording = False
        print("🛑 Force stopped recording")
    except Exception as e:
        print(f"⚠️ Force stop failed: {e}")

def action_focus_input():
    """Focus chat input (1+2)"""
    bring_browser_to_front()
    print("⌨️ Focus chat input")
    # Send Escape to focus input
    try:
        script = '''
        tell application "System Events"
            tell process "Google Chrome"
                key code 53
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
    except:
        pass

def action_upload_resume():
    """Trigger upload resume (2+3)"""
    bring_browser_to_front()
    print("📁 Upload resume/JD")
    # This would need to trigger the file input click via the frontend

def action_toggle_fast_mode():
    """Toggle fast/optimization mode (3+4)"""
    bring_browser_to_front()
    print("⚡ Toggle fast mode")
    # Send F7 to toggle
    try:
        script = '''
        tell application "System Events"
            tell process "Google Chrome"
                key code 98
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
    except:
        pass

def action_record_internal():
    """Start recording with BlackHole/internal audio (4+5)"""
    bring_browser_to_front()
    print("🔊 Recording with BlackHole (internal audio)")
    # We need to trigger this in the browser
    # For now, bring to front and let user use backtick
    time.sleep(0.2)
    action_toggle_recording()

def action_record_external():
    """Start recording with external mic (5+6)"""
    bring_browser_to_front()
    print("🎧 Recording with external mic")
    time.sleep(0.2)
    action_toggle_recording()

def action_new_chat():
    """Create new chat (Cmd+N or F8)"""
    bring_browser_to_front()
    print("💬 New chat")
    try:
        # Send Cmd+N
        script = '''
        tell application "System Events"
            tell process "Google Chrome"
                key code 45 using command down
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
    except:
        pass

def action_quick_setup():
    """Open quick setup (Cmd+Shift+S or F6)"""
    bring_browser_to_front()
    print("🚀 Quick setup")
    try:
        # Send F6
        script = '''
        tell application "System Events"
            tell process "Google Chrome"
                key code 97
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)
    except:
        pass

# ============================================================================
# Keyboard Listener
# ============================================================================

def on_press(key):
    """Handle key press"""
    global current_keys
    
    # Add to current keys
    current_keys.add(key)
    
    # Check for single key hotkeys
    try:
        if hasattr(key, 'char'):
            char = key.char
            
            # Backtick - toggle recording
            if char == '`':
                action_toggle_recording()
                return
            
            # Tilde - force stop
            if char == '~':
                action_force_stop()
                return
    except AttributeError:
        pass
    
    # Check for number combos
    keys_chars = set()
    for k in current_keys:
        if hasattr(k, 'char') and k.char:
            keys_chars.add(k.char)
    
    # 1 + 2 - Focus input
    if '1' in keys_chars and '2' in keys_chars:
        action_focus_input()
        current_keys.clear()
        return
    
    # 2 + 3 - Upload resume
    if '2' in keys_chars and '3' in keys_chars:
        action_upload_resume()
        current_keys.clear()
        return
    
    # 3 + 4 - Toggle fast mode
    if '3' in keys_chars and '4' in keys_chars:
        action_toggle_fast_mode()
        current_keys.clear()
        return
    
    # 4 + 5 - Record internal (BlackHole)
    if '4' in keys_chars and '5' in keys_chars:
        action_record_internal()
        current_keys.clear()
        return
    
    # 5 + 6 - Record external (Mic)
    if '5' in keys_chars and '6' in keys_chars:
        action_record_external()
        current_keys.clear()
        return
    
    # Check for modifier combos
    cmd_pressed = Key.cmd in current_keys or Key.cmd_l in current_keys or Key.cmd_r in current_keys
    shift_pressed = Key.shift in current_keys or Key.shift_l in current_keys or Key.shift_r in current_keys
    
    # Cmd + N - New chat
    if cmd_pressed and KeyCode.from_char('n') in current_keys:
        action_new_chat()
        current_keys.clear()
        return
    
    # Cmd + Shift + S - Quick setup
    if cmd_pressed and shift_pressed and KeyCode.from_char('s') in current_keys:
        action_quick_setup()
        current_keys.clear()
        return
    
    # Function keys
    if key == Key.f6:
        action_quick_setup()
        return
    
    if key == Key.f8:
        action_new_chat()
        return

def on_release(key):
    """Handle key release"""
    global current_keys
    
    try:
        current_keys.discard(key)
    except:
        pass
    
    # Exit on Escape + Q combo (safety exit)
    if key == Key.esc:
        # Check if Q was pressed
        if KeyCode.from_char('q') in current_keys:
            print("\n👋 Exiting global hotkey listener...")
            return False

# ============================================================================
# Main
# ============================================================================

def print_banner():
    """Print startup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🎯 Interview Assistant - Global Hotkey Listener          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  HOTKEYS (work even when browser is not focused):            ║
║                                                              ║
║  🎤 Recording:                                               ║
║     `  (backtick)    - Start/Stop recording                  ║
║     ~  (tilde)       - Force stop recording                  ║
║                                                              ║
║  ⌨️  Quick Access:                                            ║
║     1 + 2           - Focus chat input                       ║
║     2 + 3           - Upload resume/JD                       ║
║     3 + 4           - Toggle fast mode                       ║
║     4 + 5           - Record with BlackHole                  ║
║     5 + 6           - Record with Microphone                 ║
║                                                              ║
║  🚀 Commands:                                                 ║
║     Cmd + N         - New chat                               ║
║     Cmd + Shift + S - Quick setup                            ║
║     F6              - Quick setup                            ║
║     F8              - New chat                               ║
║                                                              ║
║  🛑 To exit: Press Esc + Q                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def main():
    print_banner()
    
    # Check backend connection
    print("🔌 Checking backend connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/status", timeout=2)
        if response.ok:
            print("✅ Backend connected")
        else:
            print("⚠️ Backend returned error, but continuing...")
    except:
        print("⚠️ Backend not reachable. Make sure to start the backend first!")
        print(f"   Expected at: {BACKEND_URL}")
    
    # Get current session
    session = get_current_session()
    if session:
        print(f"📋 Current session: {session}")
    else:
        print("📋 No active session (will use new session)")
    
    print("\n🎧 Listening for global hotkeys...\n")
    print("─" * 60)
    
    # Start listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()


