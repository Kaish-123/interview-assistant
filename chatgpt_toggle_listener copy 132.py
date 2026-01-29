import sys
import subprocess

import sounddevice as sd
import numpy as np
import wave
import threading
from openai import OpenAI
import tkinter as tk
from tkinter import ttk, font, filedialog
import re
import time
import queue
import textract
import pyautogui
from PIL import Image
import io
import base64
import pyperclip
from PIL import ImageGrab
from pynput import keyboard
import tempfile


from pynput import keyboard
import Quartz
import Quartz
import pyautogui
import json
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from dotenv import load_dotenv
import os


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def estimate_tokens_for_messages(messages: list, optimization_mode: bool = True) -> int:
    """Estimate token count for a list of messages."""
    tokens = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            tokens += len(content) // 4
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        tokens += len(item.get("text", "")) // 4
                    elif item.get("type") == "image_url":
                        tokens += 85 if optimization_mode else 765
    return tokens

# ============================================================================
# IMAGE OPTIMIZATION HELPERS (Safe - doesn't delete anything, just compresses)
# ============================================================================

def compress_image_for_api(image: Image.Image, max_size: int = 1024, quality: int = 85) -> str:
    """
    Compress an image for API transmission while preserving visual quality.
    - Resizes if larger than max_size (keeps aspect ratio)
    - Compresses to JPEG for smaller payload
    - Returns base64 string
    
    This reduces payload by 60-80% without losing meaningful detail for GPT.
    """
    # Resize if too large (keeping aspect ratio)
    width, height = image.size
    if width > max_size or height > max_size:
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary (for JPEG)
    if image.mode in ('RGBA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'RGBA':
            background.paste(image, mask=image.split()[3])
        else:
            background.paste(image)
        image = background
    
    # Compress to JPEG
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def compress_image_png(image: Image.Image, max_size: int = 1024) -> str:
    """
    Compress image as PNG (for screenshots with text that need sharpness).
    """
    width, height = image.size
    if width > max_size or height > max_size:
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")



# ... other imports remain the same ...
class UIPreferences:
    FILE = "ui_prefs.json"

    @staticmethod
    def load():
        try:
            if os.path.exists(UIPreferences.FILE):
                with open(UIPreferences.FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            print("UI Prefs load error:", e)
        return {}

    @staticmethod
    def save(data: dict):
        try:
            with open(UIPreferences.FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("UI Prefs save error:", e)

    
class PromptManager:
    def __init__(self, tabs_file_path="tabs.json", prompts_file_path="prompts.json"):
        self.tabs_file_path = tabs_file_path
        self.prompts_file_path = prompts_file_path
        self.data = {"tabs": []}
        self.load_tabs()

    def load_tabs(self):
        # Load tabs data from tabs.json
        if os.path.exists(self.tabs_file_path):
            try:
                with open(self.tabs_file_path, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Error loading tabs data: {str(e)}")
                self.data = {"tabs": []}
    
    def save_tabs(self):
        # Save tabs data to tabs.json
        try:
            with open(self.tabs_file_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving tabs data: {str(e)}")

    def add_tab(self, name):
        # Adds a new tab and saves it
        self.data["tabs"].append({"name": name, "subTabs": []})
        self.save_tabs()
        return len(self.data["tabs"]) - 1
    
    def add_subtab(self, tab_index, name, prompt="", text_input=""):
        # Adds a new subtab, including prompt and text_input, and saves it
        if 0 <= tab_index < len(self.data["tabs"]):
            subtab_data = {
                "name": name,
                "prompt": prompt,  # Save the prompt
                "text_input": text_input  # Save the text input
            }
            self.data["tabs"][tab_index]["subTabs"].append(subtab_data)
            self.save_tabs()  # Ensure changes are saved immediately
            return len(self.data["tabs"][tab_index]["subTabs"]) - 1
        return -1


    def get_tab_count(self):
        return len(self.data["tabs"])
    
    def get_tab_name(self, index):
        if 0 <= index < len(self.data["tabs"]):
            return self.data["tabs"][index]["name"]
        return ""
    
    def get_subtab_count(self, tab_index):
        if 0 <= tab_index < len(self.data["tabs"]):
            return len(self.data["tabs"][tab_index]["subTabs"])
        return 0
    
    def get_subtab_text_input(self, tab_index, subtab_index):
        # Retrieves the text_input from the specified subtab
        if (0 <= tab_index < len(self.data["tabs"]) and
            0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"])):
            return self.data["tabs"][tab_index]["subTabs"][subtab_index].get("text_input", "")
        return ""

    def get_subtab_name(self, tab_index, subtab_index):
        if (0 <= tab_index < len(self.data["tabs"]) and 
            0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"])):
            return self.data["tabs"][tab_index]["subTabs"][subtab_index]["name"]
        return ""
    
    def get_subtab_prompt(self, tab_index, subtab_index):
        if (0 <= tab_index < len(self.data["tabs"]) and 
            0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"])):
            return self.data["tabs"][tab_index]["subTabs"][subtab_index]["prompt"]
        return ""
    
    def update_subtab_prompt(self, tab_index, subtab_index, prompt, text_input=""):
        # Updates the prompt and text_input, then saves the data
        if 0 <= tab_index < len(self.data["tabs"]) and 0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"]):
            self.data["tabs"][tab_index]["subTabs"][subtab_index]["prompt"] = prompt
            self.data["tabs"][tab_index]["subTabs"][subtab_index]["text_input"] = text_input
            self.save_tabs()  # Save the changes
            return True
        return False



    
    def get_subtab_name(self, tab_index, subtab_index):
        if (0 <= tab_index < len(self.data["tabs"]) and 
            0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"])):
            return self.data["tabs"][tab_index]["subTabs"][subtab_index]["name"]
        return ""
    
    def get_subtab_prompt(self, tab_index, subtab_index):
        if (0 <= tab_index < len(self.data["tabs"]) and 
            0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"])):
            return self.data["tabs"][tab_index]["subTabs"][subtab_index]["prompt"]
        return ""
    
    def update_subtab_prompt(self, tab_index, subtab_index, prompt):
        if (0 <= tab_index < len(self.data["tabs"]) and 
            0 <= subtab_index < len(self.data["tabs"][tab_index]["subTabs"])):
            self.data["tabs"][tab_index]["subTabs"][subtab_index]["prompt"] = prompt
            self.save()
            return True
        return False


def get_window_under_mouse():
    mouse_x, mouse_y = pyautogui.position()
    window_info_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for window in window_info_list:
        bounds = window.get('kCGWindowBounds', {})
        x = bounds.get('X', 0)
        y = bounds.get('Y', 0)
        width = bounds.get('Width', 0)
        height = bounds.get('Height', 0)
        if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
            return window
    return None

# Example usage:
# window = get_window_under_mouse()
# if window:
#     print(f"Window under mouse: {window.get('kCGWindowName', 'No Title')}")


def get_window_list():
    window_list = []
    window_info_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for window_info in window_info_list:
        window_list.append(window_info)
    return window_list

# Example usage:
# windows = get_window_list()
# for window in windows:
#     print(window.get('kCGWindowName', 'No Title'))


def on_activate():
    if not app.assistant.recorder.is_recording:
        print("🎤 Global hotkey: Start Listening")
        app.toggle_recording()
    else:
        print("🛑 Global hotkey: Stop & Process")
        app.toggle_recording()






# Configuration
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
CHUNK = 1024
BLACKHOLE_DEVICE = "BlackHole"

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.audio_queue = queue.Queue()
        self.input_mode = "internal"  # internal = BlackHole, external = mic
        self.lock = threading.Lock()
        self.process_thread = None      # ✅ NEW

    def find_device(self):
        """
        Resolve a sounddevice input device index based on self.input_mode.

        - internal  => prefer BLACKHOLE_DEVICE
        - external  => prefer first non-BlackHole input device

        If nothing matches, return None so sounddevice uses its default.
        """
        try:
            devices = sd.query_devices()
        except Exception as e:
            print(f"⚠️ Could not query audio devices: {e}")
            return None

        target_index = None
        bh_name = BLACKHOLE_DEVICE.lower()

        if self.input_mode == "internal":
            # Prefer BlackHole for internal audio
            for idx, dev in enumerate(devices):
                try:
                    if dev.get("max_input_channels", 0) > 0 and bh_name in dev.get("name", "").lower():
                        target_index = idx
                        break
                except Exception:
                    continue
        else:
            # Prefer first *non*-BlackHole input device as "external" mic
            for idx, dev in enumerate(devices):
                try:
                    if dev.get("max_input_channels", 0) > 0 and bh_name not in dev.get("name", "").lower():
                        target_index = idx
                        break
                except Exception:
                    continue

        if target_index is None:
            print(f"⚠️ No specific device found for mode={self.input_mode!r}, falling back to default.")
            return None  # let sounddevice pick default

        try:
            print(f"🎧 Using device #{target_index}: {devices[target_index]['name']} (mode={self.input_mode})")
        except Exception:
            pass

        return target_index

    def get_snapshot(self):
        """
        Return a numpy array with all audio recorded so far (copy),
        or None if there is no audio yet.
        """
        with self.lock:
            if not self.frames:
                return None
            return np.concatenate(self.frames).copy()

    def start_recording(self):
        device_id = self.find_device()
        self.frames = []
        self.is_recording = True

        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_queue.put(indata.copy())

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
            device=device_id,
            blocksize=CHUNK
        )
        self.stream.start()
        # ✅ track the thread so we can join it on stop
        self.process_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.process_thread.start()

    def process_audio(self):
        while self.is_recording or not self.audio_queue.empty():
            try:
                frame = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            with self.lock:
                self.frames.append(frame)

    def stop_recording(self, filename="interviewer.wav"):
        # 🔚 stop callbacks first
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

        # ✅ wait for the process_audio thread to drain the queue
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)

        with self.lock:
            frames_copy = list(self.frames)

        if frames_copy:
            audio_data = np.concatenate(frames_copy)
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())
        return filename



class ChatHistoryManager:
    def __init__(self, file_path="chats.json"):
        self.file_path = file_path
        self.sessions = []  # Each item: {"title": str, "messages": List[dict]}
        self._last_save_time = 0
        self.min_save_interval = 3.0 
        self.load()
    
    def save(self, force=False):
        now = time.time()
        if not force and (now - self._last_save_time) < self.min_save_interval:
            return
        with open(self.file_path, "w") as f:
            json.dump(self.sessions, f, indent=2)
        self._last_save_time = now

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.sessions = json.load(f)
            except:
                self.sessions = []
    def save_current_session(self, messages, title="AutoSave - Last Session"):
        # 🔔 REPLACE this entire method with:
        working_session = {"title": title, "messages": messages.copy()}
        if self.sessions:
            self.sessions[0] = working_session
        else:
            self.sessions.insert(0, working_session)
        self.save()




    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.sessions, f, indent=2)

    def add_session(self, title, messages):
        self.sessions.append({"title": title, "messages": messages})
        self.save()

    def get_titles(self):
        return [s.get("title", "Untitled") for s in self.sessions]


    def get_session(self, index):
        return self.sessions[index]["messages"] if 0 <= index < len(self.sessions) else []


class ChatGPTAssistant:
    def __init__(self,app):
        self.app = app
        self.recorder = AudioRecorder()
        self.streaming = False
        self.current_response = ""
        self.messages = [{"role": "system", "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."}]
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12
        self.stream_thread = None 
        
        # ====== MODEL SETTINGS ======
        self.current_model = "gpt-4o"          # Default model (can be changed via UI)
        self.max_retries = 3                   # Number of retries for failed API calls
        
        # ====== OPTIMIZATION SETTINGS ======
        # These control how we send context to GPT while keeping FULL history locally
        self.optimization_mode = True          # Toggle for speed optimization
        self.max_rounds_for_model = 4          # Recent Q&A pairs to send (reduced from 6)
        self.summary_message = None            # Synthetic summary of older conversation
        self.summary_threshold_rounds = 5      # When to start summarizing (reduced from 8)
        self.image_detail_level = "low"        # "low" = 85 tokens, "high" = 765+ tokens
        self._summary_in_progress = False      # Prevent concurrent summarization
        self._pending_summary_thread = None    # Background summary thread
        self._system_msg_truncated = False     # Track if system msgs were truncated   
    
    def _maybe_summarize_history(self, force_sync: bool = False):
        """
        Check if summarization is needed and trigger it.
        
        Args:
            force_sync: If True and chat is very long, run synchronously (blocks but faster overall)
        """
        if not self.optimization_mode:
            return  # Skip if optimization is off
            
        if self._summary_in_progress:
            return  # Already summarizing in background
        
        # Count user/assistant messages
        user_assistant = []
        for m in self.messages:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            if role in ("user", "assistant"):
                user_assistant.append(m)

        rounds = len(user_assistant) // 2
        
        # Check if we already have a summary that's recent enough
        if self.summary_message and rounds < self.summary_threshold_rounds + 10:
            return  # Summary is still valid
        
        if rounds < self.summary_threshold_rounds:
            return  # No need yet

        # For VERY long conversations without summary, run sync to ensure we have it
        if rounds > 20 and not self.summary_message:
            print(f"⚡ IMMEDIATE summarization needed ({rounds} rounds, no summary yet)")
            self._summary_in_progress = True
            try:
                self._run_background_summary(list(user_assistant))
            finally:
                self._summary_in_progress = False
            return

        # Trigger background summarization (non-blocking!)
        self._summary_in_progress = True
        self._pending_summary_thread = threading.Thread(
            target=self._run_background_summary,
            args=(list(user_assistant),),  # Pass a copy
            daemon=True
        )
        self._pending_summary_thread.start()
        print(f"📝 Background summarization started ({rounds} rounds)")

    def _run_background_summary(self, user_assistant_msgs: list):
        """
        Runs summarization in background thread - DOES NOT BLOCK your response.
        Only updates summary_message when complete.
        """
        try:
            # 1) Build a plain-text transcript to summarize
            transcript_lines = []
            for m in user_assistant_msgs:
                role = m.get("role")
                role_label = "User" if role == "user" else "Assistant"

                content = m.get("content", "")
                if isinstance(content, list):
                    # multimodal: extract only text chunks
                    text_parts = []
                    for c in content:
                        if not isinstance(c, dict):
                            continue
                        if c.get("type") == "text":
                            text_parts.append(c.get("text", ""))
                    content = "\n".join(text_parts)
                else:
                    content = str(content)

                transcript_lines.append(f"{role_label}: {content}")

            transcript = "\n".join(transcript_lines)
            
            # Limit transcript length to avoid token limits on summary call
            if len(transcript) > 15000:
                transcript = transcript[:15000] + "\n... [truncated for summary]"

            # 2) Call a smaller/faster model to summarize
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are summarizing an ongoing job interview conversation. "
                            "Extract key points discussed: technical topics, candidate responses, "
                            "questions asked, skills mentioned, and any important context. "
                            "Be concise but preserve critical interview details."
                        ),
                    },
                    {"role": "user", "content": transcript},
                ],
                max_tokens=800  # Keep summary concise
            )
            summary_text = resp.choices[0].message.content.strip()

            # 3) Store as synthetic system message (thread-safe update)
            self.summary_message = {
                "role": "system",
                "content": f"[Interview Summary - Previous Discussion]\n{summary_text}",
            }
            print(f"✅ Background summary complete: {len(summary_text)} chars")

        except Exception as e:
            print(f"❌ Background summary error: {e}")
        finally:
            self._summary_in_progress = False


    
    def _build_messages_for_model(self):
        """
        Build optimized message list for API while preserving ALL context locally.
        
        Strategy:
        - Include system messages but TRUNCATE if very long
        - Include summary of older conversation if available
        - Include recent N rounds in full detail
        - AGGRESSIVE mode for long chats: Fewer messages, no images in old msgs
        
        This keeps your interview context complete while reducing API payload.
        """
        system_msgs = []
        other_msgs = []

        for m in self.messages:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            if role == "system":
                system_msgs.append(m)
            elif role in ("user", "assistant"):
                other_msgs.append(m)

        total_msgs = len(other_msgs)
        
        # ========== AGGRESSIVE OPTIMIZATION FOR LONG CHATS ==========
        # Determine optimization level
        if total_msgs > 50:
            keep = 6  # Only last 3 Q&A rounds
            optimization_level = "ULTRA"
        elif total_msgs > 35:
            keep = 8  # Last 4 Q&A rounds
            optimization_level = "AGGRESSIVE"
        elif total_msgs > 20:
            keep = 10  # Last 5 Q&A rounds
            optimization_level = "MODERATE"
        else:
            keep = self.max_rounds_for_model * 2
            optimization_level = "NORMAL"
        
        recent = other_msgs[-keep:] if len(other_msgs) > keep else other_msgs
        
        # If optimization mode is OFF, return everything (but still add answer mode instruction)
        if not self.optimization_mode:
            all_msgs = system_msgs + other_msgs
            if self.app and hasattr(self.app, 'get_answer_mode_instruction'):
                mode_instruction = self.app.get_answer_mode_instruction()
                if mode_instruction:
                    all_msgs.append({"role": "system", "content": mode_instruction})
            return all_msgs
        
        print(f"🔧 Optimization: {optimization_level} ({total_msgs} msgs → keeping {len(recent)})")
        
        # ========== TRUNCATE SYSTEM MESSAGES FOR VERY LONG CHATS ==========
        optimized_system = []
        MAX_SYSTEM_CHARS = 6000 if total_msgs > 40 else 10000  # Truncate for long chats
        
        for sys_msg in system_msgs:
            content = sys_msg.get("content", "")
            if len(content) > MAX_SYSTEM_CHARS:
                # Truncate long system messages (resume/JD)
                truncated = content[:MAX_SYSTEM_CHARS] + "\n... [truncated for performance]"
                optimized_system.append({"role": "system", "content": truncated})
                print(f"✂️ Truncated system message: {len(content)} → {MAX_SYSTEM_CHARS} chars")
            else:
                optimized_system.append(sys_msg)
        
        # Add summary message at the end of system messages
        if self.summary_message and self.summary_message not in optimized_system:
            optimized_system.append(self.summary_message)
        
        # ========== OPTIMIZE RECENT MESSAGES ==========
        optimized_recent = []
        for i, msg in enumerate(recent):
            optimized_msg = self._optimize_message_images(msg)
            
            # For older messages in the batch, strip images entirely (keep only text)
            # Keep images only in last 2 rounds (4 messages)
            if i < len(recent) - 4 and optimization_level in ("AGGRESSIVE", "ULTRA"):
                optimized_msg = self._strip_images_keep_text(optimized_msg)
            
            # For ULTRA mode, also truncate very long text messages
            if optimization_level == "ULTRA":
                optimized_msg = self._truncate_long_message(optimized_msg, max_chars=2000)
            
            optimized_recent.append(optimized_msg)
        
        # Add answer mode instruction if app is available
        final_messages = optimized_system + optimized_recent
        if self.app and hasattr(self.app, 'get_answer_mode_instruction'):
            mode_instruction = self.app.get_answer_mode_instruction()
            if mode_instruction:
                final_messages.append({"role": "system", "content": mode_instruction})
        
        return final_messages
    
    def _truncate_long_message(self, msg: dict, max_chars: int = 2000) -> dict:
        """Truncate very long messages while preserving structure."""
        content = msg.get("content")
        
        if isinstance(content, str) and len(content) > max_chars:
            return {"role": msg.get("role"), "content": content[:max_chars] + "... [truncated]"}
        
        if isinstance(content, list):
            truncated_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if len(text) > max_chars:
                        truncated_content.append({"type": "text", "text": text[:max_chars] + "... [truncated]"})
                    else:
                        truncated_content.append(item)
                else:
                    truncated_content.append(item)
            return {"role": msg.get("role"), "content": truncated_content}
        
        return msg
    
    def _strip_images_keep_text(self, msg: dict) -> dict:
        """
        Remove images from a message but keep all text content.
        Used for aggressive optimization of older messages.
        """
        content = msg.get("content")
        if not isinstance(content, list):
            return msg  # No images, return as-is
        
        # Extract only text items
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        
        if not text_parts:
            # If no text, add placeholder
            text_parts = ["[Image was here]"]
        
        combined_text = " ".join(text_parts)
        return {"role": msg.get("role"), "content": combined_text}
    
    def _optimize_message_images(self, msg: dict) -> dict:
        """
        Optimize images in a message by adding detail:low parameter.
        This reduces token usage from 765+ to 85 tokens per image.
        Original message is NOT modified - returns a new optimized copy.
        """
        if not self.optimization_mode:
            return msg
            
        content = msg.get("content")
        if not isinstance(content, list):
            return msg  # No images, return as-is
        
        # Create a copy with optimized images
        optimized_content = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "image_url":
                # Add detail parameter for optimization
                image_url_data = item.get("image_url", {})
                optimized_item = {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url_data.get("url", ""),
                        "detail": self.image_detail_level  # "low" = 85 tokens
                    }
                }
                optimized_content.append(optimized_item)
            else:
                optimized_content.append(item)
        
        return {"role": msg.get("role"), "content": optimized_content}


            
    def cancel_streaming(self):
        self.streaming = False
        if self.stream_thread and self.stream_thread.is_alive():
            try:
                self.stream_thread.join(timeout=1)
            except:
                pass  # Avoid crash if join fails



    def load_resume(self, file_path):
        try:
            text = textract.process(file_path).decode('utf-8')
            base = os.path.basename(file_path)

            # keep your system context line the same, or change "resume"->"document" if you prefer
            self.messages.append({
                "role": "system",
                "content": f"Use this resume content to contextualize answers (from file: {base}): {text}"
            })

            # ✅ show the actual file name in the status message
            return True, f"📄 {base} uploaded and processed successfully."
        except Exception as e:
            return False, f"❌ Error processing document: {str(e)}"


    def transcribe_audio(self, filename, prompt: str | None = None):
        """Transcribe audio with retry logic."""
        last_error = None
        
        for retry in range(self.max_retries):
            try:
                with open(filename, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        # ✅ use live preview as a hint, not as the final text
                        prompt=prompt or ""
                    )
                return transcription.text
            except Exception as e:
                last_error = e
                if retry < self.max_retries - 1:
                    wait_time = (retry + 1) * 2  # Exponential backoff
                    print(f"⚠️ Transcription failed (attempt {retry+1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    return f"❌ Transcription error after {self.max_retries} retries: {str(last_error)}"
        
        return f"❌ Transcription error: {str(last_error)}"

    def diagnose_performance(self) -> dict:
        """
        Analyze current chat for performance issues.
        Returns diagnostic info about token usage and latency sources.
        """
        diag = {
            "total_messages": len(self.messages),
            "system_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "images_count": 0,
            "estimated_total_tokens": 0,
            "estimated_system_tokens": 0,
            "estimated_conversation_tokens": 0,
            "estimated_image_tokens": 0,
            "optimization_mode": self.optimization_mode,
            "would_send_messages": 0,
            "issues": [],
            "recommendations": []
        }
        
        for msg in self.messages:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Count by role
            if role == "system":
                diag["system_messages"] += 1
                tokens = len(str(content)) // 4
                diag["estimated_system_tokens"] += tokens
            elif role == "user":
                diag["user_messages"] += 1
            elif role == "assistant":
                diag["assistant_messages"] += 1
            
            # Count images
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        diag["images_count"] += 1
                        # Image tokens: 85 (low) to 765+ (high)
                        if self.optimization_mode:
                            diag["estimated_image_tokens"] += 85
                        else:
                            diag["estimated_image_tokens"] += 765
            
            # Estimate text tokens
            if isinstance(content, str):
                diag["estimated_conversation_tokens"] += len(content) // 4
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        diag["estimated_conversation_tokens"] += len(item.get("text", "")) // 4
        
        # Calculate what would be sent
        model_msgs = self._build_messages_for_model()
        diag["would_send_messages"] = len(model_msgs)
        
        # Calculate total estimated tokens
        diag["estimated_total_tokens"] = (
            diag["estimated_system_tokens"] + 
            diag["estimated_conversation_tokens"] + 
            diag["estimated_image_tokens"]
        )
        
        # Calculate ACTUAL tokens that will be sent (using optimized messages)
        optimized_msgs = self._build_messages_for_model()
        diag["will_send_tokens"] = estimate_tokens_for_messages(optimized_msgs, self.optimization_mode)
        diag["will_send_messages"] = len(optimized_msgs)
        
        # Identify issues
        if diag["estimated_system_tokens"] > 8000:
            diag["issues"].append(f"⚠️ System messages are very large ({diag['estimated_system_tokens']} tokens)")
            diag["recommendations"].append("System messages will be auto-truncated")
        
        if diag["images_count"] > 5:
            diag["issues"].append(f"⚠️ Many images in chat ({diag['images_count']})")
            diag["recommendations"].append("Old images will be stripped automatically")
        
        if diag["total_messages"] > 20 and not self.summary_message:
            diag["issues"].append(f"⚠️ Long conversation ({diag['total_messages']} msgs) without summary")
            diag["recommendations"].append("Click 'Force Summarize' to generate summary now")
        
        if diag["will_send_tokens"] > 15000:
            diag["issues"].append(f"🔴 High token count ({diag['will_send_tokens']:,} tokens will be sent)")
            diag["recommendations"].append("Consider starting a new chat for faster responses")
        
        return diag
    
    def print_performance_report(self):
        """Print a detailed performance report to console."""
        diag = self.diagnose_performance()
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE DIAGNOSTIC REPORT")
        print("="*60)
        print(f"Total Messages: {diag['total_messages']}")
        print(f"  - System: {diag['system_messages']}")
        print(f"  - User: {diag['user_messages']}")
        print(f"  - Assistant: {diag['assistant_messages']}")
        print(f"  - Images: {diag['images_count']}")
        print()
        print(f"Estimated Tokens:")
        print(f"  - System: ~{diag['estimated_system_tokens']:,}")
        print(f"  - Conversation: ~{diag['estimated_conversation_tokens']:,}")
        print(f"  - Images: ~{diag['estimated_image_tokens']:,}")
        print(f"  - TOTAL: ~{diag['estimated_total_tokens']:,}")
        print()
        print(f"Optimization Mode: {'ON ⚡' if diag['optimization_mode'] else 'OFF 🐢'}")
        print(f"Messages sent to API: {diag['would_send_messages']}/{diag['total_messages']}")
        print(f"Has Summary: {'Yes ✅' if self.summary_message else 'No ❌'}")
        print()
        
        if diag["issues"]:
            print("⚠️ ISSUES FOUND:")
            for issue in diag["issues"]:
                print(f"  {issue}")
            print()
            print("💡 RECOMMENDATIONS:")
            for rec in diag["recommendations"]:
                print(f"  • {rec}")
        else:
            print("✅ No performance issues detected")
        
        print("="*60 + "\n")
        return diag

    def stream_gpt_response(self, text_widget, status_label, button):
        self.cancel_streaming()  # 🔴 Cancel any ongoing output

        
        def run_stream():
            # ⏱️ Start timing
            start_time = time.time()
            
            # Trigger background summarization (non-blocking - won't delay your response!)
            self._maybe_summarize_history()
            
            with self.lock:
                self.current_response = ""
                self.streaming = True
                placeholder = {"role": "assistant", "content": ""}
                self.messages.append(placeholder)

                try:
                    # ⏱️ Time message building
                    build_start = time.time()
                    
                    # ⬇️ use optimized context (keeps all system msgs + recent Q&A)
                    model_messages = self._build_messages_for_model()
                    
                    build_time = time.time() - build_start
                    
                    # Debug: show optimization stats with timing
                    total_msgs = len(self.messages)
                    sent_msgs = len(model_messages)
                    
                    # Estimate tokens in payload
                    estimated_tokens = 0
                    for m in model_messages:
                        content = m.get("content", "")
                        if isinstance(content, str):
                            estimated_tokens += len(content) // 4
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get("type") == "text":
                                        estimated_tokens += len(item.get("text", "")) // 4
                                    elif item.get("type") == "image_url":
                                        estimated_tokens += 85 if self.optimization_mode else 765
                    
                    print(f"📊 Performance: {sent_msgs}/{total_msgs} msgs, ~{estimated_tokens:,} tokens, model: {self.current_model}, build: {build_time*1000:.0f}ms")
                    
                    # ⏱️ Time API call with retry logic
                    api_start = time.time()
                    stream = None
                    last_error = None
                    
                    for retry in range(self.max_retries):
                        try:
                            stream = client.chat.completions.create(
                                model=self.current_model,
                                messages=model_messages,
                                stream=True,
                                max_tokens=1600
                            )
                            break  # Success, exit retry loop
                        except Exception as e:
                            last_error = e
                            if retry < self.max_retries - 1:
                                wait_time = (retry + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                                print(f"⚠️ API call failed (attempt {retry+1}/{self.max_retries}): {e}")
                                status_label.config(text=f"⚠️ Retrying in {wait_time}s... ({retry+1}/{self.max_retries})")
                                time.sleep(wait_time)
                            else:
                                raise last_error
                    
                    if stream is None:
                        raise Exception(f"Failed after {self.max_retries} retries: {last_error}")
                    
                    first_token_time = None

                    buffer = ""
                    last_update = time.time()

                    text_widget.config(state=tk.NORMAL)
                    text_widget.insert(tk.END, "------------------\nANSWER: ")
                    text_widget.config(state=tk.DISABLED)
                    text_widget.see(tk.END)

                    output_chars = 0
                    for chunk in stream:
                        if not self.streaming:
                            break
                        delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
                        if delta:
                            # ⏱️ Track time to first token
                            if first_token_time is None:
                                first_token_time = time.time()
                                ttft = first_token_time - api_start
                                print(f"⏱️ Time to first token: {ttft*1000:.0f}ms")
                            
                            buffer += delta
                            output_chars += len(delta)
                            self.current_response += delta
                            placeholder["content"] = self.current_response

                            if time.time() - last_update > 0.05 or len(buffer) > 20:
                                self.update_text_widget(text_widget, buffer)
                                buffer = ""
                                last_update = time.time()

                    if buffer:
                        self.update_text_widget(text_widget, buffer)
                    
                    # ⏱️ Total time
                    total_time = time.time() - start_time
                    print(f"⏱️ Total response time: {total_time:.1f}s")
                    
                    # Estimate token usage and update session cost
                    estimated_input_tokens = estimated_tokens
                    estimated_output_tokens = output_chars // 4
                    
                    # Log performance summary
                    print(f"📈 Tokens: ~{estimated_input_tokens:,} in, ~{estimated_output_tokens:,} out")

                except Exception as e:
                    placeholder["content"] = f"❌ GPT Error: {str(e)}"
                    self.update_text_widget(text_widget, f"\n{placeholder['content']}\n")

                finally:
                    self.streaming = False
                    button.config(state=tk.NORMAL)
                    status_label.config(text="✅ Ready")
                    if self.app:
                        self.app.chat_manager.save_current_session(self.messages)



        self.stream_thread = threading.Thread(target=run_stream, daemon=True)
        self.stream_thread.start()





    def update_text_widget(self, text_widget, new_text_part: str):
        # Enable the text widget for editing
        text_widget.config(state=tk.NORMAL)

        # Append only the new part of the message (delta)
        text_widget.insert(tk.END, new_text_part)

        # Auto-scroll if the user is already at the bottom
        # bottom_visible = text_widget.yview()[1] >= 0.99
        # if bottom_visible:
        #     text_widget.see(tk.END)

        # Disable the widget to make it read-only again
        text_widget.config(state=tk.DISABLED)
        text_widget.update_idletasks()




    def highlight_code(self, text_widget):
        content = text_widget.get("1.0", tk.END)
        text_widget.tag_remove('code', "1.0", tk.END)
        code_blocks = re.finditer(r'```.*?\n.*?```', content, re.DOTALL)
        for match in code_blocks:
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add('code', start, end)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("INTERVIEW ASSISTANT")

        # --- Load UI prefs first
        self.ui_prefs = UIPreferences.load()

        # Use saved geometry if present (falls back to your hardcoded one)
        self.geometry(self.ui_prefs.get("geometry", "643x967+-644+25"))

        self.toggle_lock = threading.Lock()
        self._last_persisted_hash = None

        self.is_processing_audio = False
        self.live_transcription_running = False
        self.latest_live_question = ""   # last incremental text from Whisper
        self.live_question_index = None  # index of the "Live Question" line in the Text widget
        
        # Answer Quality Mode: "default", "quick", "detailed", "code"
        self.answer_mode = "default"  # Default mode - normal GPT behavior
        
        # Multi-Model Support: Available models with descriptions
        self.available_models = {
            "gpt-4o": "🧠 GPT-4o (Best quality, slower, higher cost)",
            "gpt-4o-mini": "⚡ GPT-4o-mini (Fast, cheaper, good for simple Q&A)",
            "gpt-4-turbo": "🚀 GPT-4-Turbo (Balance of speed & quality)"
        }
        self.current_model = "gpt-4o"  # Default model
        
        # Connection status
        self.api_connected = False
        
        # Audio level tracking
        self.current_audio_level = 0
        
        # UI Mode: "modern" or "classic"
        self.ui_mode = self.ui_prefs.get("ui_mode", "modern")

        self.assistant = ChatGPTAssistant(app=self)
        self.prompt_manager = PromptManager()
        self.chat_manager = ChatHistoryManager()
        

        # If user saved a preferred font size, use it before building widgets
        if "response_font_size" in self.ui_prefs:
            self.assistant.font_size = int(self.ui_prefs["response_font_size"])

        self.setup_ui()
        self.load_chat_tabs()

        # Auto-load autosave session (unchanged)
        # Auto-load autosave session (unchanged)
        # Auto-load autosave session (safer)
        if self.chat_manager.sessions and self.chat_manager.sessions[0].get("title") == "AutoSave - Last Session":
            msgs = self.chat_manager.sessions[0].get("messages", [])
            if isinstance(msgs, list):
                self.assistant.messages = msgs
                self.display_chat_history()


            self.status.config(text="🕑 Resumed from last auto-save session")

        # Bind paste to input_entry directly (not bind_all) to prevent double-paste
        self.input_entry.bind("<Command-v>", self.handle_paste)
        self.input_entry.bind("<Control-v>", self.handle_paste)  # For non-Mac keyboards
        self.sidebar_visible = True
        self.current_tab = -1
        self.current_subtab = -1
        self.always_on_top = False

        # F1 already prints geometry
        self.bind("<F1>", lambda e: print("Window geometry:", self.geometry()))
        # 💾 New: F2 save, F3 apply
        self.bind("<F2>", lambda e: self.save_ui_prefs())
        self.bind("<F3>", lambda e: self.apply_ui_prefs())
        
        # 🚀 Quick Setup shortcut: Cmd+Shift+S (or Ctrl+Shift+S on Windows)
        self.bind("<Command-Shift-s>", lambda e: self.open_quick_setup())
        self.bind("<Control-Shift-s>", lambda e: self.open_quick_setup())
        
        # 🔖 Bookmark shortcut: Cmd+B or F4
        self.bind("<Command-b>", lambda e: self.add_bookmark_at_cursor())
        self.bind("<Control-b>", lambda e: self.add_bookmark_at_cursor())
        self.bind("<F4>", lambda e: self.add_bookmark_at_cursor())

        # Apply sash (split) after widgets exist
        self.after(0, self.apply_ui_prefs)

        # Load tabs after UI setup
        self.load_tabs()
        # Ensure we start within limits
        self.after(0, lambda: self.auto_prune_chats(max_chats=10))

    def update_live_question_in_ui(self, text: str):
        """
        Safely update the 'Live Question: ...' line in the response_box.
        This is called from a background thread via .after().
        """
        if not self.live_transcription_running:
            return

        try:
            self.response_box.config(state=tk.NORMAL)
            
            # Find "Live Question:" and replace everything after it on that line
            pos = self.response_box.search("Live Question:", "1.0", tk.END)
            if pos:
                # Get line number and delete from "Live Question:" to end of line
                line_num = pos.split('.')[0]
                self.response_box.delete(pos, f"{line_num}.end")
                # Insert the updated text
                self.response_box.insert(pos, f"Live Question: {text}")
            
            self.response_box.config(state=tk.DISABLED)
            self.response_box.see(tk.END)
        except Exception as e:
            print(f"Live UI update error: {e}")



    def live_transcription_loop(self):
        """
        Runs in a background thread while recording.
        Every ~2s, takes a snapshot of audio so far, sends it to Whisper,
        and updates the Live Question line with the latest text.
        """
        last_text = ""
        while self.live_transcription_running and self.assistant.recorder.is_recording:
            snapshot = self.assistant.recorder.get_snapshot()
            if snapshot is None:
                time.sleep(0.5)
                continue

            # Build a temporary WAV file for Whisper
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    with wave.open(tmp, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(snapshot.tobytes())
                    temp_name = tmp.name

                with open(temp_name, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                text = (transcription.text or "").strip()
            except Exception as e:
                print(f"❌ Live transcription error: {e}")
                time.sleep(1.0)
                continue
            finally:
                try:
                    os.remove(temp_name)
                except Exception:
                    pass

            if text and text != last_text:
                last_text = text
                self.latest_live_question = text
                # Schedule UI update on main thread
                self.after(0, lambda t=text: self.update_live_question_in_ui(t))

            # Small sleep to avoid too many API calls
            for _ in range(6):
                if not self.live_transcription_running or not self.assistant.recorder.is_recording:
                    break
                time.sleep(0.3)




    def auto_prune_chats(self, max_chats=10):
        """
        If there are more than `max_chats` real chats (excluding AutoSave),
        automatically delete all but the most recent real chat.
        Always keep "AutoSave - Last Session" if present.
        """
        AUTO_TITLE = "AutoSave - Last Session"

        # Split out real chats vs AutoSave
        real_indices = [i for i, s in enumerate(self.chat_manager.sessions)
                        if s.get("title") != AUTO_TITLE]
        real_count = len(real_indices)

        if real_count <= max_chats:
            return  # nothing to do

        # Keep only the MOST RECENT real chat (the last appended),
        # plus AutoSave if it exists
        keep_real_idx = real_indices[-1]  # most recent real chat by your append order
        new_sessions = []
        kept_title = None

        for i, s in enumerate(self.chat_manager.sessions):
            title = s.get("title", "Untitled")
            if i == keep_real_idx or title == AUTO_TITLE:
                new_sessions.append(s)
                if i == keep_real_idx:
                    kept_title = title

        removed_count = len(self.chat_manager.sessions) - len(new_sessions)
        if removed_count > 0:
            self.chat_manager.sessions = new_sessions
            self.chat_manager.save()
            self.load_chat_tabs()

            # Reselect the kept real chat if it exists, otherwise select AutoSave
            reselect_index = 0
            for i, s in enumerate(self.chat_manager.sessions):
                if s.get("title", "") == kept_title:
                    reselect_index = i
                    break
            kept_item_id = f"chat_{reselect_index}"
            if self.chat_tabs.exists(kept_item_id):
                self.chat_tabs.selection_set(kept_item_id)
                self.chat_tabs.see(kept_item_id)

            self.status.config(
                text=f"🧹 Auto-pruned {removed_count} chat(s). Kept recent chat{f' “{kept_title}”' if kept_title else ''} and “{AUTO_TITLE}”."
            )


    def _get_tree_open_state(self, tree: ttk.Treeview):
        """Return a list of item IDs that are expanded (open=True) in the given Treeview."""
        open_iids = []

        def walk(iid):
            try:
                if tree.item(iid, 'open'):
                    open_iids.append(iid)
            except Exception:
                pass
            for child in tree.get_children(iid):
                walk(child)

        # top-level nodes
        for root in tree.get_children(''):
            walk(root)

        return open_iids


    def _apply_tree_open_state(self, tree: ttk.Treeview, open_iids):
        """Expand items whose IDs are in open_iids (ignore any that don't exist)."""
        if not open_iids:
            return
        def do_apply():
            for iid in open_iids:
                if tree.exists(iid):
                    tree.item(iid, open=True)
        # Apply now and once more shortly after, in case the tree was just rebuilt
        self.after(0, do_apply)
        self.after(120, do_apply)

    def _generate_session_title(self):
        """Create a nice title for the current chat, reusing your start_new_chat logic."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Look for any resume attachment in system messages
        resume_name = None
        for msg in self.assistant.messages:
            if not isinstance(msg, dict):
                continue
            if msg.get("role") != "system":
                continue

            content = msg.get("content", "")
            if not isinstance(content, str):
                continue

            if "Use this resume content to contextualize answers" in content:
                match = re.search(r'from file:\s*(.+?)\)', content)
                if match:
                    resume_name = os.path.splitext(
                        os.path.basename(match.group(1).strip())
                    )[0]
                break

        if resume_name:
            return f"{resume_name} - {timestamp}"
        return timestamp


    def _persist_working_chat_if_needed(self):
        """
        If current working chat has user content and is not already saved as a real session
        (i.e., beyond 'AutoSave - Last Session'), save it now as a new session.
        """
        msgs = self.assistant.messages or []
        # Must have at least one user message to be meaningful
        if not any(m.get("role") == "user" for m in msgs):
            return

        # Optional: use a hash to avoid saving exact duplicates repeatedly
        try:
            # Convert messages to a JSON string deterministically for hashing
            payload = json.dumps(msgs, sort_keys=True, ensure_ascii=False)
            cur_hash = hash(payload)
            if self._last_persisted_hash is not None and self._last_persisted_hash == cur_hash:
                return  # nothing new since last persist
        except Exception:
            cur_hash = None  # fall back to linear check

        # Avoid duplicates: if an identical non-AutoSave session already exists, skip
        for s in self.chat_manager.sessions:
            if s.get("title") != "AutoSave - Last Session" and s.get("messages") == msgs:
                # already saved
                self._last_persisted_hash = cur_hash
                return

        # Save as a proper session with a generated title
        title = self._generate_session_title()
        self.chat_manager.add_session(title, msgs.copy())
        self.chat_manager.save()
        self.load_chat_tabs()
        # 🔁 Auto-prune when over the limit
        self.auto_prune_chats(max_chats=10)


        self.status.config(text=f"💾 Saved current chat as: {title}")
        self._last_persisted_hash = cur_hash


    def load_tabs(self):
        self.tab_tree.delete(*self.tab_tree.get_children())

        for i in range(self.prompt_manager.get_tab_count()):
            tab_id = self.tab_tree.insert("", "end", text=self.prompt_manager.get_tab_name(i), iid=f"tab_{i}")
            for j in range(self.prompt_manager.get_subtab_count(i)):
                subtab_id = self.tab_tree.insert(tab_id, "end", text=self.prompt_manager.get_subtab_name(i, j), iid=f"sub_{i}_{j}")

        # # Automatically select first subtab if available
        # if self.prompt_manager.get_tab_count() > 0 and self.prompt_manager.get_subtab_count(0) > 0:
        #     self.tab_tree.selection_set(f"sub_0_0")
        #     self.after(100, lambda: self.on_tab_select(None))  # Trigger selection logic

    def save_ui_prefs(self):
        """Save current window geometry, split position, font size, and tabs/subtabs open state."""
        try:
            sash = self.paned.sashpos(0)
        except Exception:
            sash = None
        
        # Save sidebar internal split (tabs vs chats)
        try:
            sidebar_sash = self.sidebar_paned.sashpos(0)
        except Exception:
            sidebar_sash = None

        prefs = {
            "geometry": self.geometry(),
            "paned_sash": sash,
            "sidebar_sash": sidebar_sash,  # NEW: tabs/chats split position
            "response_font_size": int(self.assistant.font_size),
            # NEW: expanded ("open") items in the tabs/subtasks tree
            "tab_tree_open": self._get_tree_open_state(self.tab_tree),
        }
        UIPreferences.save(prefs)
        self.status.config(text="💾 Saved UI defaults (geometry, splits, font, dropdowns).")
        print("Saved UI Prefs:", prefs)


    def apply_ui_prefs(self, *_):
        """Apply saved defaults (geometry, split, font size, tabs/subtabs open state)."""
        prefs = self.ui_prefs = UIPreferences.load()

        # Geometry
        if "geometry" in prefs:
            try:
                self.geometry(prefs["geometry"])
            except Exception as e:
                print("Geometry apply error:", e)

        # Font
        if "response_font_size" in prefs:
            try:
                self.assistant.font_size = int(prefs["response_font_size"])
                self.response_box.config(font=('Consolas', self.assistant.font_size))
            except Exception as e:
                print("Font apply error:", e)

        # Main split (sidebar vs main content)
        if "paned_sash" in prefs and prefs["paned_sash"] is not None:
            try:
                self.paned.sashpos(0, int(prefs["paned_sash"]))
            except Exception as e:
                print("Sash apply error, retrying...", e)
                self.after(50, lambda: self.paned.sashpos(0, int(prefs["paned_sash"])))

        # Sidebar internal split (tabs vs chats)
        if "sidebar_sash" in prefs and prefs["sidebar_sash"] is not None:
            def apply_sidebar_sash():
                try:
                    self.sidebar_paned.sashpos(0, int(prefs["sidebar_sash"]))
                except Exception as e:
                    print("Sidebar sash apply error:", e)
            self.after(100, apply_sidebar_sash)  # Delay to ensure widget is ready

        # NEW: tabs/subtabs expanded state
        if "tab_tree_open" in prefs:
            self._apply_tree_open_state(self.tab_tree, prefs["tab_tree_open"])

        self.status.config(text="✅ Applied UI defaults.")


        
    def on_chat_tab_select(self, event):
        selected = self.chat_tabs.selection()
        if not selected:
            return

        # ✅ Ensure the working chat is saved before switching away
        self._persist_working_chat_if_needed()

        tab_id = selected[0]
        if tab_id.startswith("chat_"):
            index = int(tab_id.split("_")[1])
            self.assistant.messages = self.chat_manager.get_session(index)
            self.display_chat_history()
            self.status.config(text=f"📂 Loaded chat: {self.chat_manager.get_titles()[index]}")

    def add_new_tab(self):
        name = simpledialog.askstring("New Tab", "Enter tab name:")
        if name:
            tab_index = self.prompt_manager.add_tab(name)
            self.tab_tree.insert("", "end", text=name, iid=f"tab_{tab_index}")
            self.add_subtab_btn.config(state=tk.NORMAL)

        
    def toggle_input_mode(self):
        if self.assistant.recorder.input_mode == "internal":
            self.assistant.recorder.input_mode = "external"
            self.toggle_input_btn.config(text="🎧 Mic")
            self.status.config(text="🎧 Switched to External Microphone")
        else:
            self.assistant.recorder.input_mode = "internal"
            self.toggle_input_btn.config(text="🔈 BlackHole")
            self.status.config(text="🔈 Switched to Internal Audio (BlackHole)")

    # ========== CONNECTION STATUS ==========
    def check_api_connection(self):
        """Check if OpenAI API is reachable."""
        def _check():
            try:
                # Quick test call to check connectivity
                response = client.models.list()
                self.api_connected = True
                self.after(0, lambda: self.connection_label.config(text="🟢 Connected"))
            except Exception as e:
                self.api_connected = False
                self.after(0, lambda: self.connection_label.config(text="🔴 Offline"))
                print(f"API Connection check failed: {e}")
        
        threading.Thread(target=_check, daemon=True).start()
        # Re-check every 60 seconds
        self.after(60000, self.check_api_connection)

    # ========== MULTI-MODEL SUPPORT ==========
    def toggle_model(self):
        """Cycle through available models with description."""
        models = list(self.available_models.keys())
        model_labels = {
            "gpt-4o": "🧠 4o",
            "gpt-4o-mini": "⚡ Mini",
            "gpt-4-turbo": "🚀 Turbo"
        }
        
        current_idx = models.index(self.current_model)
        next_idx = (current_idx + 1) % len(models)
        self.current_model = models[next_idx]
        
        # Update button and show description
        self.model_btn.config(text=model_labels[self.current_model])
        self.status.config(text=f"🔄 Model: {self.available_models[self.current_model]}")
        
        # Update the assistant's model
        self.assistant.current_model = self.current_model

    # ========== UI MODE TOGGLE ==========
    def toggle_ui_mode(self):
        """Toggle between modern and classic UI mode (requires restart)."""
        if self.ui_mode == "modern":
            self.ui_mode = "classic"
            msg = "🎨 Classic UI mode selected. Restart app to apply."
        else:
            self.ui_mode = "modern"
            msg = "🎨 Modern UI mode selected. Restart app to apply."
        
        # Save preference
        self.ui_prefs["ui_mode"] = self.ui_mode
        UIPreferences.save(self.ui_prefs)
        self.status.config(text=msg)
        
        # Ask if user wants to restart now
        if messagebox.askyesno("UI Mode Changed", f"{msg}\n\nRestart now?"):
            self._restart_app()
    
    def _restart_app(self):
        """Restart the application."""
        import subprocess
        try:
            python = sys.executable
            script = os.path.abspath(sys.argv[0])
            subprocess.Popen([python, script])
            self.destroy()
            os._exit(0)
        except Exception as e:
            self.status.config(text=f"❌ Restart failed: {e}")

    # ========== AUDIO LEVEL INDICATOR ==========
    def update_audio_level(self):
        """Update the audio level indicator during recording."""
        if not self.assistant.recorder.is_recording:
            self.audio_level_bar['value'] = 0
            self.audio_level_label.config(text="--")
            return
        
        # Get current audio level from recorder
        snapshot = self.assistant.recorder.get_snapshot()
        if snapshot is not None and len(snapshot) > 0:
            # Calculate RMS level
            rms = np.sqrt(np.mean(snapshot[-1600:]**2))  # Last 0.1 sec
            # Convert to percentage (normalize to reasonable range)
            level = min(100, int(rms / 300 * 100))
            self.current_audio_level = level
            self.audio_level_bar['value'] = level
            self.audio_level_label.config(text=f"{level}%")
        
        # Continue updating while recording
        if self.assistant.recorder.is_recording:
            self.after(100, self.update_audio_level)

    def toggle_answer_mode(self):
        """Cycle through answer quality modes: Default → Quick → Detailed → Code → Default"""
        modes = ["default", "quick", "detailed", "code"]
        mode_labels = {
            "default": "🔘 Default",
            "quick": "⚡ Quick",
            "detailed": "📝 Detailed", 
            "code": "💻 Code"
        }
        mode_descriptions = {
            "default": "Normal GPT behavior",
            "quick": "Short, concise answers",
            "detailed": "Comprehensive explanations",
            "code": "Focus on code examples"
        }
        
        # Cycle to next mode
        current_idx = modes.index(self.answer_mode)
        next_idx = (current_idx + 1) % len(modes)
        self.answer_mode = modes[next_idx]
        
        # Update button text
        self.answer_mode_btn.config(text=mode_labels[self.answer_mode])
        self.status.config(text=f"🎯 Answer Mode: {mode_descriptions[self.answer_mode]}")

    def get_answer_mode_instruction(self):
        """Return instruction text based on current answer mode"""
        instructions = {
            "default": "",  # No special instruction - normal GPT behavior
            "quick": "\n\n[INSTRUCTION: Provide SHORT, CONCISE answers like a real human expert would in a conversation. Be brief and natural. IMPORTANT: Sound like a real person - avoid AI phrases like 'Certainly!', 'I'd be happy to', 'As an AI'. Don't be overly formal or structured. Just answer naturally like a knowledgeable colleague would. Maximum 2-3 sentences.]",
            "detailed": "\n\n[INSTRUCTION: Provide COMPREHENSIVE explanations like a senior developer explaining to a teammate. IMPORTANT: Sound completely HUMAN - avoid typical AI patterns like 'Certainly!', 'Great question!', 'I'd be happy to help', 'As an AI'. Don't use excessive bullet points or overly structured formats. Speak naturally, use casual professional tone, include real-world context. Explain like you're a human expert having a conversation, not a chatbot giving a formal response.]",
            "code": "\n\n[INSTRUCTION: Focus on CODE EXAMPLES. Provide working code snippets with brief explanations. Prioritize practical, copy-paste ready code.]"
        }
        return instructions.get(self.answer_mode, "")

    def display_chat_history(self, max_rounds=20):
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)

        # Normalize / skip malformed messages
        ua = []
        for m in self.assistant.messages:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            if role in ("user", "assistant"):
                ua.append(m)

        # keep last max_rounds * 2 msgs
        keep = max_rounds * 2
        recent_ua = ua[-keep:] if len(ua) > keep else ua

        for msg in recent_ua:
            role = msg.get("role")
            content = msg.get("content", "")

            # Normalize content to text
            if isinstance(content, list):
                text = "\n".join(
                    c.get("text", "[non-text]")
                    if c.get("type") == "text"
                    else "[Image]"
                    for c in content
                )
            else:
                text = str(content)

            if role == "user":
                self.response_box.insert(
                    tk.END,
                    f"\n\n---------------------------------------------------------------------\nQUESTION: {text.strip()}\n"
                )
            elif role == "assistant":
                self.response_box.insert(
                    tk.END,
                    f"------------------\nANSWER: {text.strip()}\n"
                )

        self.response_box.config(state=tk.DISABLED)
        self.response_box.see(tk.END)



    def setup_ui(self):
        # Create paned window for sidebar and main content
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        # Create sidebar frame
        self.sidebar = ttk.Frame(self.paned, width=200)
        self.paned.add(self.sidebar, weight=0)
        
        # Create toggle button at top
        self.toggle_btn = ttk.Button(self.sidebar, text="☰", width=2, command=self.toggle_sidebar)
        self.toggle_btn.pack(pady=5, fill="x")

        # ====== RESIZABLE SIDEBAR SECTIONS ======
        # Create a vertical PanedWindow inside sidebar for resizable sections
        self.sidebar_paned = ttk.PanedWindow(self.sidebar, orient=tk.VERTICAL)
        self.sidebar_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ----- TOP SECTION: Tabs/Subtabs -----
        self.tab_section = ttk.Frame(self.sidebar_paned)
        self.sidebar_paned.add(self.tab_section, weight=2)  # Gets more space by default
        
        ttk.Label(self.tab_section, text="📋 Prompts & Subtabs").pack(anchor="w")
        
        # Create tab treeview with scrollbar
        self.tab_frame = ttk.Frame(self.tab_section)
        self.tab_frame.pack(fill="both", expand=True)
        
        self.tab_tree = ttk.Treeview(self.tab_frame, show="tree", selectmode="browse")
        self.tab_tree.pack(fill="both", expand=True, side="left")
        self.tab_tree.bind("<<TreeviewSelect>>", self.on_tab_select)
        
        # Add drag-and-drop for tabs/subtabs
        self._setup_drag_drop(self.tab_tree, "tabs")
        
        # Add scrollbar to tab_tree
        tab_scrollbar = ttk.Scrollbar(self.tab_frame, orient="vertical", command=self.tab_tree.yview)
        tab_scrollbar.pack(side="right", fill="y")
        self.tab_tree.configure(yscrollcommand=tab_scrollbar.set)

        # ----- BOTTOM SECTION: Chat History -----
        self.chat_section = ttk.Frame(self.sidebar_paned)
        self.sidebar_paned.add(self.chat_section, weight=1)  # Gets less space by default
        
        ttk.Label(self.chat_section, text="💬 Past Chats").pack(anchor="w")
        
        # Create chat history treeview with scrollbar
        self.chat_frame = ttk.Frame(self.chat_section)
        self.chat_frame.pack(fill="both", expand=True)
        
        self.chat_tabs = ttk.Treeview(self.chat_frame, show="tree", selectmode="browse")
        self.chat_tabs.pack(fill="both", expand=True, side="left")
        self.chat_tabs.bind("<<TreeviewSelect>>", self.on_chat_tab_select)
        
        # Add drag-and-drop for chats
        self._setup_drag_drop(self.chat_tabs, "chats")
        
        # Add scrollbar to chat_tabs
        chat_scrollbar = ttk.Scrollbar(self.chat_frame, orient="vertical", command=self.chat_tabs.yview)
        chat_scrollbar.pack(side="right", fill="y")
        self.chat_tabs.configure(yscrollcommand=chat_scrollbar.set)

        # Create buttons frame
        btn_frame = ttk.Frame(self.sidebar)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.add_tab_btn = ttk.Button(btn_frame, text="+ Tab", command=self.add_new_tab)
        self.add_tab_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.add_subtab_btn = ttk.Button(btn_frame, text="+ Sub", command=self.add_new_subtab, state=tk.DISABLED)
        self.add_subtab_btn.pack(side="left", fill="x", expand=True, padx=2)
        
        # Quick Setup button for multi-select subtabs
        self.quick_setup_btn = ttk.Button(btn_frame, text="🚀", command=self.open_quick_setup, width=3)
        self.quick_setup_btn.pack(side="left", padx=2)
        
        self.delete_chat_btn = ttk.Button(self.sidebar, text="🗑 Delete Chat", command=self.delete_chat)
        self.delete_chat_btn.pack(side="left", padx=4)

        self.rename_chat_btn = ttk.Button(self.sidebar, text="✏️ Rename Chat", command=self.rename_chat)
        self.rename_chat_btn.pack(side="left", padx=4)


        # Create main content frame (existing UI)
        self.main_frame = ttk.Frame(self.paned)
        self.paned.add(self.main_frame, weight=1)

        # ====== HEADER BAR ======
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", padx=10, pady=(5, 2))
        
        # Connection status (left)
        self.connection_label = ttk.Label(header_frame, text="🔴", font=('Arial', 10))
        self.connection_label.pack(side="left", padx=(0, 5))
        
        # Main status label (left-center)
        self.status = ttk.Label(header_frame, text="🔊 Ready", font=('Arial', 10))
        self.status.pack(side="left", padx=5)
        
        # Audio level indicator (right)
        self.audio_level_frame = ttk.Frame(header_frame)
        self.audio_level_frame.pack(side="right", padx=5)
        ttk.Label(self.audio_level_frame, text="🎙", font=('Arial', 9)).pack(side="left")
        self.audio_level_bar = ttk.Progressbar(self.audio_level_frame, length=60, mode='determinate', maximum=100)
        self.audio_level_bar.pack(side="left", padx=2)
        self.audio_level_label = ttk.Label(self.audio_level_frame, text="--", font=('Arial', 8), width=4)
        self.audio_level_label.pack(side="left")
        
        # Check API connection on startup
        self.after(500, self.check_api_connection)

        text_frame = ttk.Frame(self.main_frame)
        text_frame.pack(fill="both", expand=True, padx=10)

        # ====== BOOKMARK/POINTER PANEL (like debug breakpoints) ======
        # Pack FIRST (side=right) so it reserves space before response_box expands
        self.bookmark_frame = ttk.Frame(text_frame, width=28)
        self.bookmark_frame.pack(side="right", fill="y", padx=(2, 0))
        self.bookmark_frame.pack_propagate(False)
        
        # Bookmark header with tooltip
        bookmark_header = ttk.Label(self.bookmark_frame, text="📍", font=('Arial', 9))
        bookmark_header.pack(pady=1)
        
        # Bookmark listbox (shows pointers)
        self.bookmark_listbox = tk.Listbox(
            self.bookmark_frame, 
            bg='#2d2d30', 
            fg='#ffd700',  # Gold color for pointers
            selectbackground='#4a4a00',
            selectforeground='#ffff00',
            font=('Arial', 8),
            width=3,
            highlightthickness=0,
            borderwidth=0
        )
        self.bookmark_listbox.pack(fill="both", expand=True)
        self.bookmark_listbox.bind("<<ListboxSelect>>", self._on_bookmark_click)
        self.bookmark_listbox.bind("<Double-Button-1>", self._on_bookmark_delete)
        
        # Store bookmarks: [(line_index, question_preview), ...]
        self.bookmarks = []

        # Scrollbar - pack second (side=right)
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        # Response box - pack last (side=left, expand) takes remaining space
        self.response_box = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
                                    bg='#343541', fg='white', insertbackground='white', selectbackground='#4E4E4E',
                                    highlightthickness=0)
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.insert(tk.END, "🤖 Start a new conversation or ask your first question...")
        self.response_box.config(state=tk.DISABLED, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.response_box.yview)
        
        self.response_box.tag_configure('code', foreground='#4EC9B0')
        self.response_box.tag_configure('bookmark_highlight', background='#4a4a00', foreground='#ffff00')
        
        # Right-click context menu for bookmarking
        self.response_box.bind("<Button-2>", self._show_bookmark_menu)  # Middle click on Mac
        self.response_box.bind("<Button-3>", self._show_bookmark_menu)  # Right click
        self.response_box.bind("<Control-Button-1>", self._show_bookmark_menu)  # Ctrl+click on Mac

        # ====== MODERN CONTROL PANEL - 2 ROWS ======
        control_container = ttk.Frame(self.main_frame)
        control_container.pack(fill="x", padx=10, pady=5)
        
        # ----- ROW 1: MAIN ACTIONS (Recording & Chat) -----
        row1 = ttk.Frame(control_container)
        row1.pack(fill="x", pady=(0, 3))
        
        # LEFT: Primary actions
        self.record_btn = ttk.Button(row1, text="🎤 Listen", command=self.toggle_recording, width=10)
        self.record_btn.pack(side="left", padx=2)
        
        self.stop_btn = ttk.Button(row1, text="⏹ Stop", command=self.stop_output, state=tk.DISABLED, width=8)
        self.stop_btn.pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(row1, orient="vertical").pack(side="left", fill="y", padx=8)
        
        self.new_chat_btn = ttk.Button(row1, text="🆕 New Chat", command=self.start_new_chat, width=10)
        self.new_chat_btn.pack(side="left", padx=2)
        
        self.upload_btn = ttk.Button(row1, text="📁 Resume/JD", command=self.upload_resume, width=10)
        self.upload_btn.pack(side="left", padx=2)
        
        # RIGHT: Window controls
        self.topmost_btn = ttk.Button(row1, text="📌", command=self.toggle_always_on_top, width=3)
        self.topmost_btn.pack(side="right", padx=2)
        
        # UI Mode toggle (Classic/Modern)
        self.ui_mode_btn = ttk.Button(row1, text="🎨", command=self.toggle_ui_mode, width=3)
        self.ui_mode_btn.pack(side="right", padx=2)
        
        # ----- ROW 2: SETTINGS & OPTIONS -----
        row2 = ttk.Frame(control_container)
        row2.pack(fill="x", pady=(0, 0))
        
        # Model selector
        self.model_btn = ttk.Button(row2, text="🧠 4o", command=self.toggle_model, width=7)
        self.model_btn.pack(side="left", padx=2)
        
        # Answer mode
        self.answer_mode_btn = ttk.Button(row2, text="🔘 Default", command=self.toggle_answer_mode, width=10)
        self.answer_mode_btn.pack(side="left", padx=2)
        
        # Fast mode
        self.optimize_btn = ttk.Button(row2, text="⚡ Fast", command=self.toggle_optimization_mode, width=7)
        self.optimize_btn.pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=8)
        
        # Audio input toggle (compact)
        self.toggle_input_btn = ttk.Button(row2, text="🔈 BlackHole", command=self.toggle_input_mode, width=10)
        self.toggle_input_btn.pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=8)
        
        # Bookmarks
        self.bookmark_btn = ttk.Button(row2, text="🔖", command=self.add_bookmark_at_cursor, width=3)
        self.bookmark_btn.pack(side="left", padx=2)
        
        self.clear_bookmarks_btn = ttk.Button(row2, text="🗑", command=self.clear_all_bookmarks, width=3)
        self.clear_bookmarks_btn.pack(side="left", padx=2)
        
        # Report button
        self.diag_btn = ttk.Button(row2, text="📊", command=self.show_performance_dialog, width=3)
        self.diag_btn.pack(side="left", padx=2)
        
        # RIGHT: Font controls
        font_frame = ttk.Frame(row2)
        font_frame.pack(side="right", padx=2)
        ttk.Button(font_frame, text="A+", command=self.increase_font, width=3).pack(side="left")
        ttk.Button(font_frame, text="A-", command=self.decrease_font, width=3).pack(side="left")

        # ====== INPUT BAR (bottom) ======
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=8)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 13))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.input_entry.bind("<Return>", lambda event: self.submit_text_question())

        self.submit_btn = ttk.Button(input_frame, text="Send ➡️", width=8, command=self.submit_text_question)
        self.submit_btn.pack(side="right")

    def load_chat_tabs(self):
        print("Chat Tabs:", self.chat_tabs)  # Debugging line
        self.chat_tabs.delete(*self.chat_tabs.get_children())
        for i, title in enumerate(self.chat_manager.get_titles()):
            self.chat_tabs.insert("", "end", iid=f"chat_{i}", text=title)
            
    def delete_chat(self):
        """
        Delete ALL chats except:
            - the currently selected chat
            - the "AutoSave - Last Session" chat
        """
        AUTO_TITLE = "AutoSave - Last Session"

        # Require a selection to know which one to keep (the 'current chat')
        selected = self.chat_tabs.selection()
        if not selected:
            messagebox.showwarning("No Chat Selected", "Please select the chat you want to KEEP.")
            return

        tab_id = selected[0]
        if not tab_id.startswith("chat_"):
            messagebox.showwarning("Invalid Selection", "Please select a valid chat.")
            return

        keep_index = int(tab_id.split("_")[1])
        titles = self.chat_manager.get_titles()
        if keep_index < 0 or keep_index >= len(titles):
            messagebox.showwarning("Invalid Selection", "Selected chat index is out of range.")
            return

        keep_title = titles[keep_index]

        # Build the new chat list, keeping only the selected chat and the AutoSave session (if present)
        original_count = len(self.chat_manager.sessions)
        new_sessions = []
        for i, s in enumerate(self.chat_manager.sessions):
            title = s.get("title", "Untitled")
            if i == keep_index or title == AUTO_TITLE:
                new_sessions.append(s)

        removed_count = original_count - len(new_sessions)
        if removed_count <= 0:
            messagebox.showinfo("Nothing to Delete", "There are no other chats to delete.")
            return

        confirm = messagebox.askyesno(
            "Delete Chats",
            f"This will permanently delete {removed_count} chat(s), keeping only:\n\n"
            f"• {keep_title}\n"
            f"• {AUTO_TITLE} (if it exists)\n\n"
            "Are you sure?"
        )
        if not confirm:
            return

        # Commit changes
        self.chat_manager.sessions = new_sessions
        self.chat_manager.save()

        # Refresh UI list
        self.load_chat_tabs()

        # Reselect the kept chat (find it again by title)
        reselect_index = 0
        for i, s in enumerate(self.chat_manager.sessions):
            if s.get("title", "") == keep_title:
                reselect_index = i
                break
        kept_item_id = f"chat_{reselect_index}"
        if self.chat_tabs.exists(kept_item_id):
            self.chat_tabs.selection_set(kept_item_id)
            self.chat_tabs.see(kept_item_id)

        self.status.config(text=f"🧹 Deleted {removed_count} chat(s). Kept: “{keep_title}” and “{AUTO_TITLE}”.")
        print(f"Deleted {removed_count} chat(s). Kept: {keep_title} (index {reselect_index}) and '{AUTO_TITLE}'.")


    def rename_chat(self):
        selected = self.chat_tabs.selection()
        if not selected:
            messagebox.showwarning("No Chat Selected", "Please select a chat first")
            return

        # Get the chat index from the selected tab
        tab_id = selected[0]
        if tab_id.startswith("chat_"):
            index = int(tab_id.split("_")[1])
            old_title = self.chat_manager.get_titles()[index]

            # Ask for a new name
            new_name = simpledialog.askstring("Rename Chat", f"Enter a new name for the chat '{old_title}':")
            if new_name:
                # Update the title in the chat history manager
                self.chat_manager.sessions[index]["title"] = new_name
                self.chat_manager.save()

                # Update the chat tab title in the UI
                self.chat_tabs.item(tab_id, text=new_name)

                self.status.config(text=f"🔄 Renamed chat to: {new_name}")
                print(f"Renamed chat to: {new_name}")



    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible

        if self.sidebar_visible:
            self.paned.forget(self.mini_sidebar)  # Remove mini toggle
            self.paned.insert(0, self.sidebar)    # Restore full sidebar
        else:
            self.paned.forget(self.sidebar)       # Remove full sidebar

            # Add a minimal sidebar with just the ☰ button
            self.mini_sidebar = ttk.Frame(self.paned, width=30)
            toggle_only_btn = ttk.Button(self.mini_sidebar, text="☰", command=self.toggle_sidebar, width=2)
            toggle_only_btn.pack(padx=2, pady=5, fill="x")
            self.paned.insert(0, self.mini_sidebar)



    def add_new_tab(self):
        name = simpledialog.askstring("New Tab", "Enter tab name:")
        if name:
            tab_index = self.prompt_manager.add_tab(name)
            self.tab_tree.insert("", "end", text=name, iid=f"tab_{tab_index}")
            self.add_subtab_btn.config(state=tk.NORMAL)

    def add_new_subtab(self):
    # Get selected tab
        selected = self.tab_tree.selection()
        if not selected:
            messagebox.showwarning("No Tab Selected", "Please select a tab first")
            return
                
        tab_id = selected[0]
        if not tab_id.startswith("tab_"):
            # Find parent tab
            parent = self.tab_tree.parent(tab_id)
            if parent:
                tab_id = parent
        
        if tab_id.startswith("tab_"):
            tab_index = int(tab_id.split("_")[1])
            name = simpledialog.askstring("New Subtask", "Enter subtab name:")
            if name:
                prompt = simpledialog.askstring("Prompt", "Enter prompt text:")
                
                # Use the prompt text as both the prompt and text_input
                text_input = prompt  # Directly use the prompt text as the input for this subtab

                subtab_index = self.prompt_manager.add_subtab(tab_index, name, prompt or "", text_input or "")
                self.tab_tree.insert(tab_id, "end", text=name, iid=f"sub_{tab_index}_{subtab_index}")

    # ============================================================================
    # QUICK SETUP - Multi-select subtabs and send in ONE message
    # ============================================================================
    
    def open_quick_setup(self):
        """Open Quick Setup dialog with multi-select subtabs and profiles."""
        dialog = tk.Toplevel(self)
        dialog.title("🚀 Quick Setup - Interview Initialization")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (600 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # ---- PROFILES SECTION ----
        profile_frame = ttk.LabelFrame(dialog, text="📋 Saved Profiles (One-Click Apply)")
        profile_frame.pack(fill="x", padx=10, pady=5)
        
        profiles = self._load_setup_profiles()
        self._profile_vars = {}
        
        profile_btn_frame = ttk.Frame(profile_frame)
        profile_btn_frame.pack(fill="x", padx=5, pady=5)
        
        if profiles:
            for i, (name, subtab_ids) in enumerate(profiles.items()):
                btn = ttk.Button(
                    profile_btn_frame, 
                    text=f"▶ {name}", 
                    command=lambda n=name, s=subtab_ids, d=dialog: self._apply_profile(n, s, d)
                )
                btn.pack(side="left", padx=2, pady=2)
                if i >= 4:  # Limit visible profiles
                    break
        else:
            ttk.Label(profile_btn_frame, text="No saved profiles yet", foreground="gray").pack()
        
        # ---- SUBTABS SELECTION ----
        select_frame = ttk.LabelFrame(dialog, text="☑️ Select Prompts to Apply (multi-select)")
        select_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollable canvas for checkboxes
        canvas = tk.Canvas(select_frame)
        scrollbar = ttk.Scrollbar(select_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create checkboxes for each tab/subtab
        self._setup_checkboxes = {}  # {subtab_id: (var, text)}
        
        for tab_idx in range(self.prompt_manager.get_tab_count()):
            tab_name = self.prompt_manager.get_tab_name(tab_idx)
            
            # Tab header
            tab_label = ttk.Label(scrollable_frame, text=f"📁 {tab_name}", font=('Arial', 11, 'bold'))
            tab_label.pack(anchor="w", pady=(10, 2), padx=5)
            
            # Subtabs
            for sub_idx in range(self.prompt_manager.get_subtab_count(tab_idx)):
                sub_name = self.prompt_manager.get_subtab_name(tab_idx, sub_idx)
                sub_text = self.prompt_manager.get_subtab_text_input(tab_idx, sub_idx) or \
                           self.prompt_manager.get_subtab_prompt(tab_idx, sub_idx) or sub_name
                
                var = tk.BooleanVar(value=False)
                subtab_id = f"sub_{tab_idx}_{sub_idx}"
                self._setup_checkboxes[subtab_id] = (var, sub_text, sub_name)
                
                cb = ttk.Checkbutton(
                    scrollable_frame, 
                    text=f"  {sub_name}", 
                    variable=var
                )
                cb.pack(anchor="w", padx=20)
        
        # ---- ACTION BUTTONS ----
        action_frame = ttk.Frame(dialog)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        # Select/Deselect All
        ttk.Button(
            action_frame, 
            text="☑ Select All", 
            command=lambda: self._toggle_all_checkboxes(True)
        ).pack(side="left", padx=2)
        
        ttk.Button(
            action_frame, 
            text="☐ Deselect All", 
            command=lambda: self._toggle_all_checkboxes(False)
        ).pack(side="left", padx=2)
        
        ttk.Separator(action_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # Save as Profile
        ttk.Button(
            action_frame, 
            text="💾 Save Profile", 
            command=lambda: self._save_current_as_profile(dialog)
        ).pack(side="left", padx=2)
        
        # Apply button (main action)
        apply_btn = ttk.Button(
            action_frame, 
            text="🚀 APPLY SELECTED", 
            command=lambda: self._apply_quick_setup(dialog),
            style="Accent.TButton"
        )
        apply_btn.pack(side="right", padx=2)
        
        # Status label
        self._setup_status = ttk.Label(dialog, text="Select prompts and click Apply to send in ONE message")
        self._setup_status.pack(pady=5)
        
        # Keyboard shortcut
        dialog.bind("<Return>", lambda e: self._apply_quick_setup(dialog))
        dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    def _toggle_all_checkboxes(self, select: bool):
        """Select or deselect all checkboxes."""
        for subtab_id, (var, _, _) in self._setup_checkboxes.items():
            var.set(select)
    
    def _load_setup_profiles(self) -> dict:
        """Load saved setup profiles from file."""
        profile_path = os.path.join(os.path.dirname(__file__), "setup_profiles.json")
        try:
            if os.path.exists(profile_path):
                with open(profile_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading profiles: {e}")
        return {}
    
    def _save_setup_profiles(self, profiles: dict):
        """Save setup profiles to file."""
        profile_path = os.path.join(os.path.dirname(__file__), "setup_profiles.json")
        try:
            with open(profile_path, "w") as f:
                json.dump(profiles, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
    
    def _save_current_as_profile(self, dialog):
        """Save currently selected subtabs as a profile."""
        selected = [sid for sid, (var, _, _) in self._setup_checkboxes.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one prompt to save as profile")
            return
        
        name = simpledialog.askstring("Save Profile", "Enter profile name:", parent=dialog)
        if name:
            profiles = self._load_setup_profiles()
            profiles[name] = selected
            self._save_setup_profiles(profiles)
            self._setup_status.config(text=f"✅ Profile '{name}' saved with {len(selected)} prompts!")
            messagebox.showinfo("Saved", f"Profile '{name}' saved!\nReopen Quick Setup to use it.")
    
    def _apply_profile(self, profile_name: str, subtab_ids: list, dialog):
        """Apply a saved profile - select checkboxes and apply."""
        # First, deselect all
        self._toggle_all_checkboxes(False)
        
        # Select the ones in the profile
        for subtab_id in subtab_ids:
            if subtab_id in self._setup_checkboxes:
                self._setup_checkboxes[subtab_id][0].set(True)
        
        # Auto-apply
        self._apply_quick_setup(dialog)
    
    def _apply_quick_setup(self, dialog):
        """Combine selected prompts and send in ONE message."""
        selected_texts = []
        selected_names = []
        
        for subtab_id, (var, text, name) in self._setup_checkboxes.items():
            if var.get():
                selected_texts.append(text)
                selected_names.append(name)
        
        if not selected_texts:
            messagebox.showwarning("No Selection", "Please select at least one prompt")
            return
        
        # Combine all prompts into ONE message
        combined_prompt = "\n\n---\n\n".join(selected_texts)
        
        # Close dialog
        dialog.destroy()
        
        # Show confirmation in status
        self.status.config(text=f"🚀 Applying {len(selected_texts)} prompts in ONE message...")
        
        # Add to input entry (in case user wants to add more)
        current = self.input_entry.get().strip()
        if current:
            combined_prompt = f"{current}\n\n{combined_prompt}"
        
        self.input_entry.delete(0, tk.END)
        
        # Build content array
        content = [{"type": "text", "text": combined_prompt}]
        
        # Include any pending attachments (images)
        if hasattr(self, 'pending_attachments'):
            content.extend(self.pending_attachments)
            del self.pending_attachments
        
        # Display in response box
        display_text = f"[Quick Setup: {', '.join(selected_names[:3])}{'...' if len(selected_names) > 3 else ''}]"
        self.response_box.config(state=tk.NORMAL)
        self.response_box.insert(
            tk.END,
            f"\n\n---------------------------------------------------------------------\n"
            f"🚀 QUICK SETUP: {display_text}\n"
            f"Applying {len(selected_texts)} prompts...\n"
        )
        self.response_box.config(state=tk.DISABLED)
        self.response_box.see(tk.END)
        
        # Send to GPT
        if any(c["type"] == "image_url" for c in content):
            self.assistant.messages.append({"role": "user", "content": content})
        else:
            self.assistant.messages.append({"role": "user", "content": combined_prompt})
        
        # Save and stream
        self.chat_manager.save_current_session(self.assistant.messages)
        self.assistant.cancel_streaming()
        self.assistant.stream_gpt_response(self.response_box, self.status, self.record_btn)
        
        self.status.config(text=f"✅ Applied {len(selected_texts)} prompts!")

    def on_tab_select(self, event):
        # Reentrancy guard (TreeviewSelect can fire more than once)
        if getattr(self, "_subtab_sending", False):
            return

        selected = self.tab_tree.selection()
        if not selected:
            self.current_tab = -1
            self.current_subtab = -1
            return

        item_id = selected[0]

        # Tab (top level) clicked: just remember selection; do not send
        if item_id.startswith("tab_"):
            self.current_tab = int(item_id.split("_")[1])
            self.current_subtab = -1
            self.add_subtab_btn.config(state=tk.NORMAL)
            return

        # Only handle subtab clicks from here on
        if not item_id.startswith("sub_"):
            return

        parts = item_id.split("_")
        self.current_tab = int(parts[1])
        self.current_subtab = int(parts[2])
        self.add_subtab_btn.config(state=tk.NORMAL)

        # Prefer text_input, then prompt, then subtab name
        sub_name   = self.prompt_manager.get_subtab_name(self.current_tab, self.current_subtab) or "Request"
        prompt     = self.prompt_manager.get_subtab_prompt(self.current_tab, self.current_subtab) or ""
        text_input = self.prompt_manager.get_subtab_text_input(self.current_tab, self.current_subtab) or ""
        sub_text   = (text_input or prompt or sub_name).strip()

        # If nothing found, still send the subtab name as a fallback
        if not sub_text:
            sub_text = sub_name

        # Append sub_text to whatever is already in the entry (do NOT wipe)
        current = self.input_entry.get()
        prefix = "" if (not current or current.endswith((" ", "\n", "\t"))) else " "
        self.input_entry.insert(tk.END, f"{prefix}{sub_text}")

        # Auto-send the combined message (existing text + subchat text + any queued images)
        try:
            self._subtab_sending = True  # guard
            # submit_text_question() will:
            #  - read the entry,
            #  - include self.pending_attachments (if any),
            #  - clear entry & attachments,
            #  - stream the response.
            self.submit_text_question()

            # UX hint
            if hasattr(self, "pending_attachments"):
                # (submit_text_question clears pending_attachments after sending)
                pass
            self.status.config(text="🚀 Sub chat sent with your current text and any attached image(s).")
        finally:
            self._subtab_sending = False




        
    def handle_paste(self, event=None):
        # 1) Try text first
        try:
            text = self.clipboard_get()
            if isinstance(text, str) and text.strip():
                # ✅ Append text at caret, do not clear previous input or attachments
                self.input_entry.insert(tk.INSERT, text)
                # keep any queued attachments
                return "break"
        except tk.TclError:
            # no text in clipboard; try image next
            pass
        except Exception as e:
            print(f"❌ Paste (text) failed: {e}")
            self.status.config(text=f"❌ Paste error: {e}")
            # fall through to image

        # 2) Try image
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                # Compress image for faster transmission and lower token cost
                b64_image = compress_image_png(image, max_size=1280)
                original_size = image.size[0] * image.size[1] * 3 // 1024  # Rough KB estimate
                compressed_size = len(b64_image) // 1024
                print(f"📎 Image compressed: ~{original_size}KB → {compressed_size}KB")

                # ✅ Keep a growing list of attachments
                if not hasattr(self, 'pending_attachments'):
                    self.pending_attachments = []

                self.pending_attachments.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                })

                # ✅ Insert a placeholder at caret (don't wipe existing text)
                idx = len(self.pending_attachments)
                self.input_entry.insert(tk.INSERT, f" [📎 Image {idx}] ")

                self.status.config(text=f"📎 {idx} image(s) attached ({compressed_size}KB). Paste more or Enter to send.")
                return "break"
        except Exception as e:
            print(f"❌ Paste (image) failed: {e}")
            self.status.config(text=f"❌ Paste error: {e}")

        # Let native paste happen if neither text nor image detected
        return None





    # def setup_ui(self):
    #     self.status = ttk.Label(self, text="🔊 Ready", style='TLabel')
    #     self.status.pack(pady=5, anchor="w", padx=10)
        


    #     text_frame = ttk.Frame(self)
    #     text_frame.pack(fill="both", expand=True, padx=10)

    #     self.response_box = tk.Text(
    #         text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
    #         bg='#343541', fg='white', insertbackground='white',
    #         selectbackground='#4E4E4E', highlightthickness=0
    #     )
    #     self.response_box.pack(side="left", fill="both", expand=True)
    #     self.response_box.insert(tk.END, "🤖 Start a new conversation or ask your first question...")
    #     self.response_box.config(state=tk.DISABLED)
    #     self.response_box.tag_configure('code', foreground='#4EC9B0')

    #     scrollbar = ttk.Scrollbar(text_frame, command=self.response_box.yview)
    #     scrollbar.pack(side="right", fill="y")
    #     self.response_box.config(yscrollcommand=scrollbar.set)

    #     # Button bar above chat entry
    #     control_frame = ttk.Frame(self)
    #     control_frame.pack(fill="x", padx=10, pady=5)

    #     self.record_btn = ttk.Button(control_frame, text="🎤 Listen", command=self.toggle_recording)
    #     self.record_btn.pack(side="left", padx=4)
        
    #     self.toggle_input_btn = ttk.Button(control_frame, text="🔈 Internal Audio (BlackHole)", command=self.toggle_input_mode)
    #     self.toggle_input_btn.pack(side="left", padx=4)
        
        

    #     self.new_chat_btn = ttk.Button(control_frame, text="🆕 New", command=self.start_new_chat)
    #     self.new_chat_btn.pack(side="left", padx=4)

    #     self.stop_btn = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_output, state=tk.DISABLED)
    #     self.stop_btn.pack(side="left", padx=4)

    #     self.upload_btn = ttk.Button(control_frame, text="📁 Resume", command=self.upload_resume)
    #     self.upload_btn.pack(side="left", padx=4)

    #     font_controls = ttk.Frame(control_frame)
    #     font_controls.pack(side="left", padx=10)
    #     ttk.Button(font_controls, text="A+", command=self.increase_font).pack(side="left")
    #     ttk.Button(font_controls, text="A-", command=self.decrease_font).pack(side="left")
        
        


    #     self.topmost_btn = ttk.Button(control_frame, text="📌 Pin", command=self.toggle_always_on_top)
    #     self.topmost_btn.pack(side="right", padx=4)

    #     # Chat input bar at bottom
    #     input_frame = ttk.Frame(self)
    #     input_frame.pack(side="bottom", fill="x", padx=10, pady=5)

    #     self.input_entry = ttk.Entry(input_frame, font=('Arial', 14), width=80)
    #     self.input_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))

    #     self.input_entry.bind("<Return>", lambda event: self.submit_text_question())

    #     self.submit_btn = ttk.Button(input_frame, text="➡️", width=4, command=self.submit_text_question)
    #     self.submit_btn.pack(side="right")
        
    #     self.load_chat_tabs()

    def capture_and_submit_screenshot(self):
        self.status.config(text="📸 Capturing screen...")
        print("📸 Got the screen capture")

        screenshot = pyautogui.screenshot()
        
        # Use compressed image for faster transmission
        b64_image = compress_image_png(screenshot, max_size=1280)
        print(f"📸 Screenshot compressed: {len(b64_image) // 1024}KB")

        # Build multimodal message (text + image)
        content = [
            {"type": "text", "text": "Please analyze this screenshot."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
        ]

        # UI preview
        self.response_box.config(state=tk.NORMAL)
        self.response_box.insert(
            tk.END,
            "\n\n---------------------------------------------------------------------\nQUESTION: [Screenshot attached]\n"
        )
        self.response_box.config(state=tk.DISABLED)
        self.response_box.see(tk.END)

        # Add to chat history & stream
        self.assistant.messages.append({"role": "user", "content": content})
        self.chat_manager.save_current_session(self.assistant.messages)

        self.status.config(text="🧠 Analyzing screenshot...")
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(self.response_box, self.status, self.record_btn),
            daemon=True
        ).start()


    def submit_text_question(self):
        question = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)

        # If nothing to send at all
        if not question and not hasattr(self, 'pending_attachments'):
            return

        # Screenshot shortcut remains
        if question == "--":
            self.capture_and_submit_screenshot()
            return

        content = []

        # ✅ Always include text if present
        if question:
            content.append({"type": "text", "text": question})

        # ✅ Always include any queued images
        if hasattr(self, 'pending_attachments'):
            content.extend(self.pending_attachments)
            del self.pending_attachments  # clear only after sending

        # Flatten for UI display
        flat_text = "\n".join(
            c["text"] if c["type"] == "text" else "[Image]" for c in content
        )

        self.response_box.config(state=tk.NORMAL)
        self.response_box.insert(
            tk.END,
            f"\n\n---------------------------------------------------------------------\nQUESTION: {flat_text.strip()}\n"
        )
        self.response_box.config(state=tk.DISABLED)
        self.response_box.see(tk.END)

        # Send to GPT
        if any(c["type"] == "image_url" for c in content):
            self.assistant.messages.append({"role": "user", "content": content})
        else:
            self.assistant.messages.append({"role": "user", "content": flat_text})

        # Mark as dirty so auto-persist can save if you switch chats
        self._last_persisted_hash = None

        self.chat_manager.save_current_session(self.assistant.messages)
        self.assistant.cancel_streaming()
        self.assistant.stream_gpt_response(self.response_box, self.status, self.record_btn)



            
        def capture_and_submit_screenshot(self):
            self.status.config(text="📸 Capturing screen...")
            print("📸 Got the screen capture")

            screenshot = pyautogui.screenshot()
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            buffer.seek(0)

            self.assistant.messages.append({
                "role": "user",
                "content": [{"type": "text", "text": "Please analyze this screenshot."},
                            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + buffer.getvalue().decode('latin1')}}]
            })
            self.status.config(text="🧠 Analyzing screenshot...")
            threading.Thread(
                target=self.assistant.stream_gpt_response,
                args=(self.response_box, self.status, self.record_btn),
                daemon=True
            ).start()



    def upload_resume(self):
        file_path = filedialog.askopenfilename(title="Select Resume File", filetypes=[("All Files", "*.*")])
        if file_path:
            success, message = self.assistant.load_resume(file_path)
            self.status.config(text=message)

    def toggle_recording(self):
        with self.toggle_lock:
            if self.is_processing_audio:
                # Instead of blocking, we now force a reset if the user explicitly tries to record
                print("⚡️ Interrupting ongoing processing for new recording.")
                self.stop_output()                # Trigger stop
                self.is_processing_audio = False  # Reset
                self.assistant.streaming = False
                self.assistant.current_response = ""

            if not self.assistant.recorder.is_recording:
                self.assistant.streaming = False

                # Show listening + create a Live Question line
                self.response_box.config(state=tk.NORMAL)
                self.response_box.insert(tk.END, "\n\n🎙 Listening to your question...\n")
                # Remember where the live question line starts
                self.live_question_index = self.response_box.index(tk.END)
                self.response_box.insert(tk.END, "Live Question: ")
                self.response_box.config(state=tk.DISABLED)
                self.response_box.see(tk.END)

                self.assistant.recorder.start_recording()
                self.status.config(text="🎙 Listening to interviewer...")
                self.record_btn.config(text="🛑 Stop & Process")
                self.stop_btn.config(state=tk.DISABLED)

                # 🔴 Start live / incremental transcription
                self.live_transcription_running = True
                threading.Thread(target=self.live_transcription_loop, daemon=True).start()
                
                # 🎙 Start audio level indicator
                self.after(100, self.update_audio_level)

            else:
                self.is_processing_audio = True  # Set flag to True when processing audio
                self.record_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.status.config(text="💭 Processing question...")
                threading.Thread(target=self.process_recording, daemon=True).start()



    def process_recording(self):
        # Stop live transcription immediately
        self.live_transcription_running = False
        
        try:
            self.status.config(text="⏳ Getting complete question...")
            
            # Stop recording and get the audio file - captures ALL audio until this moment
            filename = self.assistant.recorder.stop_recording()
            
            # ALWAYS do final transcription on the COMPLETE audio file
            # This ensures we get every word until the ` button was pressed
            question = self.assistant.transcribe_audio(filename)

            if not question or question.startswith("❌"):
                self.status.config(text=question if question else "⚠️ No speech detected")
                return
            
            question = question.strip()

            # Clean up the "Listening..." block from UI before showing final question
            self.response_box.config(state=tk.NORMAL)
            content = self.response_box.get("1.0", tk.END)
            listening_idx = content.rfind("🎙 Listening to your question...")
            if listening_idx != -1:
                self.response_box.delete(f"1.0+{listening_idx}c", tk.END)
            self.response_box.config(state=tk.DISABLED)

            # Show the final question in UI (only once)
            self.response_box.config(state=tk.NORMAL)
            self.response_box.insert(tk.END, f"\n\n---------------------------------------------------------------------\nQUESTION: {question}\n")
            self.response_box.config(state=tk.DISABLED)
            self.response_box.see(tk.END)

            # Send to GPT (only once)
            self.assistant.messages.append({"role": "user", "content": question})
            self.chat_manager.save_current_session(self.assistant.messages)

            self.status.config(text="💡 Generating answer...")
            self.assistant.cancel_streaming()
            self.assistant.stream_gpt_response(self.response_box, self.status, self.record_btn)
            self.chat_manager.save_current_session(self.assistant.messages)

        finally:
            self.is_processing_audio = False  # Reset the flag after processing is complete






    def start_new_chat(self):
        # Save current session if not empty
        if any(isinstance(m, dict) and m.get("role") == "user" for m in self.assistant.messages):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # Look for any resume attachment in system messages
            resume_name = None
            for msg in self.assistant.messages:
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "system":
                    continue

                content = msg.get("content", "")
                if not isinstance(content, str):
                    continue

                if "Use this resume content to contextualize answers" in content:
                    match = re.search(r'from file:\s*(.+?)\)', content)
                    if match:
                        resume_name = os.path.splitext(
                            os.path.basename(match.group(1).strip())
                        )[0]
                    break

            # Compose title using resume name if available
            if resume_name:
                session_title = f"{resume_name} - {timestamp}"
            else:
                session_title = timestamp

            self.chat_manager.add_session(session_title, self.assistant.messages.copy())
            self.chat_manager.save()
            self.load_chat_tabs()
            # 🔁 Auto-prune when over the limit
            self.auto_prune_chats(max_chats=10)

        # Start fresh session
        self.assistant.messages = [{
            "role": "system",
            "content": "You are a helpful interview assistant. "
                       "Provide detailed technical answers and ask follow-up questions when appropriate."
        }]
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, "🤖 New conversation started...")
        self.response_box.config(state=tk.DISABLED)
        self.status.config(text="🆕 New chat started")




    def stop_output(self):
        self.assistant.streaming = False
        self.stop_btn.config(state=tk.DISABLED)
        self.status.config(text="⏹ Output stopped")

    def increase_font(self):
        self.assistant.font_size = min(24, self.assistant.font_size + 1)
        self.response_box.config(font=('Consolas', self.assistant.font_size))

    def decrease_font(self):
        self.assistant.font_size = max(8, self.assistant.font_size - 1)
        self.response_box.config(font=('Consolas', self.assistant.font_size))

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.attributes("-topmost", self.always_on_top)
        self.topmost_btn.config(text="📌 Unpin Window" if self.always_on_top else "📌 Pin Window")
    
    def show_performance_dialog(self):
        """Show performance diagnostic dialog."""
        diag = self.assistant.diagnose_performance()
        self.assistant.print_performance_report()  # Also print to console
        
        dialog = tk.Toplevel(self)
        dialog.title("📊 Performance Diagnostics")
        dialog.geometry("450x500")
        dialog.transient(self)
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Header
        ttk.Label(dialog, text="📊 Performance Analysis", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(dialog, text="Current Chat Statistics")
        stats_frame.pack(fill="x", padx=15, pady=5)
        
        stats = [
            (f"Total Messages:", f"{diag['total_messages']}"),
            (f"  System:", f"{diag['system_messages']}"),
            (f"  User:", f"{diag['user_messages']}"),
            (f"  Assistant:", f"{diag['assistant_messages']}"),
            (f"  Images:", f"{diag['images_count']}"),
        ]
        
        for label, value in stats:
            row = ttk.Frame(stats_frame)
            row.pack(fill="x", padx=10, pady=2)
            ttk.Label(row, text=label).pack(side="left")
            ttk.Label(row, text=value, font=('Arial', 10, 'bold')).pack(side="right")
        
        # Token estimate frame
        token_frame = ttk.LabelFrame(dialog, text="Token Usage (Full Chat vs Optimized)")
        token_frame.pack(fill="x", padx=15, pady=5)
        
        token_stats = [
            ("Full Chat Tokens:", f"~{diag['estimated_total_tokens']:,}", diag['estimated_total_tokens'] > 30000),
            ("→ WILL SEND:", f"~{diag.get('will_send_tokens', 0):,} tokens", diag.get('will_send_tokens', 0) > 15000),
        ]
        
        for label, value, is_warning in token_stats:
            row = ttk.Frame(token_frame)
            row.pack(fill="x", padx=10, pady=2)
            ttk.Label(row, text=label).pack(side="left")
            color = 'red' if is_warning else 'green' if '→' in label else 'black'
            ttk.Label(row, text=value, font=('Arial', 10, 'bold'), foreground=color).pack(side="right")
        
        # Show reduction percentage
        if diag['estimated_total_tokens'] > 0:
            reduction = (1 - diag.get('will_send_tokens', 0) / diag['estimated_total_tokens']) * 100
            reduction_row = ttk.Frame(token_frame)
            reduction_row.pack(fill="x", padx=10, pady=2)
            ttk.Label(reduction_row, text="Token Reduction:").pack(side="left")
            ttk.Label(reduction_row, text=f"{reduction:.0f}% saved!", 
                      font=('Arial', 10, 'bold'), foreground='green').pack(side="right")
        
        # Optimization status
        opt_frame = ttk.LabelFrame(dialog, text="Optimization Status")
        opt_frame.pack(fill="x", padx=15, pady=5)
        
        opt_row = ttk.Frame(opt_frame)
        opt_row.pack(fill="x", padx=10, pady=5)
        opt_status = "⚡ ON (Fast Mode)" if diag['optimization_mode'] else "🐢 OFF (Full Context)"
        ttk.Label(opt_row, text="Mode:").pack(side="left")
        ttk.Label(opt_row, text=opt_status, font=('Arial', 10, 'bold')).pack(side="right")
        
        sent_row = ttk.Frame(opt_frame)
        sent_row.pack(fill="x", padx=10, pady=2)
        ttk.Label(sent_row, text="Messages sent to API:").pack(side="left")
        ttk.Label(sent_row, text=f"{diag['would_send_messages']}/{diag['total_messages']}", 
                  font=('Arial', 10, 'bold')).pack(side="right")
        
        has_summary = "Yes ✅" if self.assistant.summary_message else "No ❌"
        sum_row = ttk.Frame(opt_frame)
        sum_row.pack(fill="x", padx=10, pady=2)
        ttk.Label(sum_row, text="Has Summary:").pack(side="left")
        ttk.Label(sum_row, text=has_summary, font=('Arial', 10, 'bold')).pack(side="right")
        
        # Issues and recommendations
        if diag["issues"]:
            issues_frame = ttk.LabelFrame(dialog, text="⚠️ Issues Found")
            issues_frame.pack(fill="x", padx=15, pady=5)
            
            for issue in diag["issues"]:
                ttk.Label(issues_frame, text=issue, wraplength=400).pack(anchor="w", padx=10, pady=2)
            
            ttk.Label(issues_frame, text="\n💡 Recommendations:", font=('Arial', 10, 'bold')).pack(anchor="w", padx=10)
            for rec in diag["recommendations"]:
                ttk.Label(issues_frame, text=f"• {rec}", wraplength=400).pack(anchor="w", padx=20, pady=1)
        else:
            ttk.Label(dialog, text="✅ No performance issues detected!", 
                      font=('Arial', 11, 'bold'), foreground='green').pack(pady=10)
        
        # Action buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def force_summarize():
            self.assistant._maybe_summarize_history()
            self.status.config(text="🔄 Triggering background summarization...")
            dialog.destroy()
        
        ttk.Button(btn_frame, text="🔄 Force Summarize", command=force_summarize).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🆕 New Chat", command=lambda: [self.start_new_chat(), dialog.destroy()]).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side="left", padx=5)
    
    # ============================================================================
    # BOOKMARK/POINTER SYSTEM - Quick navigation to questions (like debug breakpoints)
    # ============================================================================
    
    def add_bookmark_at_cursor(self):
        """
        Add a bookmark at the nearest QUESTION in the response box.
        Searches backward from current view to find 'QUESTION:' line.
        """
        try:
            # Get current visible position
            visible_start = self.response_box.index("@0,0")
            
            # Search backward for "QUESTION:" from current view
            question_pos = self.response_box.search(
                "QUESTION:", 
                visible_start, 
                backwards=True, 
                stopindex="1.0"
            )
            
            # If not found backwards, search forward
            if not question_pos:
                question_pos = self.response_box.search(
                    "QUESTION:", 
                    visible_start, 
                    forwards=True, 
                    stopindex=tk.END
                )
            
            if not question_pos:
                # No question found, bookmark current visible line
                question_pos = visible_start
                self._add_bookmark(question_pos, "📍 Manual mark")
            else:
                # Get the question text (rest of that line)
                line_end = f"{question_pos.split('.')[0]}.end"
                question_text = self.response_box.get(question_pos, line_end).strip()
                
                # Truncate for display
                if len(question_text) > 40:
                    question_text = question_text[:37] + "..."
                
                self._add_bookmark(question_pos, question_text)
                
        except Exception as e:
            print(f"Bookmark error: {e}")
            self.status.config(text=f"❌ Bookmark error: {e}")
    
    def add_bookmark_at_position(self, line_index: str, preview: str = ""):
        """Add a bookmark at a specific position (called programmatically)."""
        self._add_bookmark(line_index, preview or f"Q at line {line_index.split('.')[0]}")
    
    def _add_bookmark(self, line_index: str, preview: str):
        """Internal method to add a bookmark."""
        # Check if already bookmarked (same line)
        line_num = line_index.split('.')[0]
        for existing_idx, _ in self.bookmarks:
            if existing_idx.split('.')[0] == line_num:
                self.status.config(text="⚠️ This line is already bookmarked")
                return
        
        # Add to bookmarks list
        bookmark_num = len(self.bookmarks) + 1
        self.bookmarks.append((line_index, preview))
        
        # Add to listbox (show number)
        self.bookmark_listbox.insert(tk.END, f"Q{bookmark_num}")
        
        # Highlight the bookmarked line in response box
        self._highlight_bookmark(line_index)
        
        self.status.config(text=f"🔖 Bookmark #{bookmark_num} added: {preview[:30]}...")
        print(f"📍 Bookmark #{bookmark_num} at {line_index}: {preview}")
    
    def _highlight_bookmark(self, line_index: str):
        """Highlight a bookmarked line in the response box."""
        try:
            line_num = line_index.split('.')[0]
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            
            self.response_box.config(state=tk.NORMAL)
            self.response_box.tag_add('bookmark_highlight', line_start, line_end)
            self.response_box.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Highlight error: {e}")
    
    def _on_bookmark_click(self, event=None):
        """Jump to the selected bookmark."""
        selection = self.bookmark_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx < len(self.bookmarks):
            line_index, preview = self.bookmarks[idx]
            
            # Jump to that line
            self.response_box.see(line_index)
            
            # Flash highlight the line briefly
            self._flash_bookmark(line_index)
            
            self.status.config(text=f"📍 Jumped to: {preview[:40]}...")
    
    def _flash_bookmark(self, line_index: str):
        """Flash a bookmark line to draw attention."""
        try:
            line_num = line_index.split('.')[0]
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            
            # Create flash tag
            self.response_box.tag_configure('bookmark_flash', background='#ffff00', foreground='#000000')
            
            self.response_box.config(state=tk.NORMAL)
            self.response_box.tag_add('bookmark_flash', line_start, line_end)
            self.response_box.config(state=tk.DISABLED)
            
            # Remove flash after 500ms
            self.after(500, lambda: self._remove_flash(line_start, line_end))
        except Exception as e:
            print(f"Flash error: {e}")
    
    def _remove_flash(self, start, end):
        """Remove the flash highlight."""
        try:
            self.response_box.config(state=tk.NORMAL)
            self.response_box.tag_remove('bookmark_flash', start, end)
            self.response_box.config(state=tk.DISABLED)
        except:
            pass
    
    def _on_bookmark_delete(self, event=None):
        """Delete a bookmark on double-click."""
        selection = self.bookmark_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx < len(self.bookmarks):
            line_index, preview = self.bookmarks[idx]
            
            # Remove highlight
            try:
                line_num = line_index.split('.')[0]
                self.response_box.config(state=tk.NORMAL)
                self.response_box.tag_remove('bookmark_highlight', f"{line_num}.0", f"{line_num}.end")
                self.response_box.config(state=tk.DISABLED)
            except:
                pass
            
            # Remove from list
            del self.bookmarks[idx]
            self.bookmark_listbox.delete(idx)
            
            # Renumber remaining bookmarks
            self._renumber_bookmarks()
            
            self.status.config(text=f"🗑 Bookmark removed: {preview[:30]}...")
    
    def _renumber_bookmarks(self):
        """Renumber bookmarks after deletion."""
        self.bookmark_listbox.delete(0, tk.END)
        for i, (_, _) in enumerate(self.bookmarks):
            self.bookmark_listbox.insert(tk.END, f"Q{i+1}")
    
    def clear_all_bookmarks(self):
        """Clear all bookmarks."""
        if not self.bookmarks:
            self.status.config(text="ℹ️ No bookmarks to clear")
            return
        
        # Remove all highlights
        try:
            self.response_box.config(state=tk.NORMAL)
            self.response_box.tag_remove('bookmark_highlight', "1.0", tk.END)
            self.response_box.config(state=tk.DISABLED)
        except:
            pass
        
        # Clear list
        self.bookmarks.clear()
        self.bookmark_listbox.delete(0, tk.END)
        
        self.status.config(text="🗑 All bookmarks cleared")
    
    def auto_bookmark_question(self, question_text: str):
        """
        Automatically add a bookmark when a new question is submitted.
        Called from submit_text_question or process_recording.
        """
        try:
            # Find the latest "QUESTION:" in the response box
            end_pos = self.response_box.index(tk.END)
            question_pos = self.response_box.search(
                "QUESTION:", 
                end_pos, 
                backwards=True, 
                stopindex="1.0"
            )
            
            if question_pos:
                preview = question_text[:40] + "..." if len(question_text) > 40 else question_text
                self._add_bookmark(question_pos, f"QUESTION: {preview}")
        except Exception as e:
            print(f"Auto-bookmark error: {e}")
    
    def _show_bookmark_menu(self, event):
        """Show context menu for bookmarking at click position."""
        # Get click position in text widget
        click_index = self.response_box.index(f"@{event.x},{event.y}")
        line_num = click_index.split('.')[0]
        
        # Get line content
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"
        line_text = self.response_box.get(line_start, line_end).strip()
        
        # Create popup menu
        menu = tk.Menu(self, tearoff=0)
        
        # Check if this line is already bookmarked
        is_bookmarked = any(idx.split('.')[0] == line_num for idx, _ in self.bookmarks)
        
        if is_bookmarked:
            menu.add_command(
                label="🗑 Remove Bookmark", 
                command=lambda: self._remove_bookmark_at_line(line_num)
            )
        else:
            preview = line_text[:30] + "..." if len(line_text) > 30 else line_text
            menu.add_command(
                label=f"🔖 Bookmark Here", 
                command=lambda: self._add_bookmark(line_start, preview or f"Line {line_num}")
            )
        
        menu.add_separator()
        
        # Find nearest question
        nearest_q = self.response_box.search("QUESTION:", click_index, backwards=True, stopindex="1.0")
        if nearest_q:
            q_line = nearest_q.split('.')[0]
            q_text = self.response_box.get(nearest_q, f"{q_line}.end").strip()[:25]
            menu.add_command(
                label=f"🔖 Mark Question: {q_text}...", 
                command=lambda: self._add_bookmark(nearest_q, q_text)
            )
        
        menu.add_separator()
        menu.add_command(label="📋 Show All Questions", command=self._show_all_questions_dialog)
        
        # Show menu at click position
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _remove_bookmark_at_line(self, line_num: str):
        """Remove bookmark at a specific line."""
        for i, (idx, _) in enumerate(self.bookmarks):
            if idx.split('.')[0] == line_num:
                # Remove highlight
                try:
                    self.response_box.config(state=tk.NORMAL)
                    self.response_box.tag_remove('bookmark_highlight', f"{line_num}.0", f"{line_num}.end")
                    self.response_box.config(state=tk.DISABLED)
                except:
                    pass
                
                del self.bookmarks[i]
                self._renumber_bookmarks()
                self.status.config(text=f"🗑 Bookmark removed")
                return
    
    def _show_all_questions_dialog(self):
        """Show a dialog with all questions for easy bookmarking."""
        dialog = tk.Toplevel(self)
        dialog.title("📋 All Questions - Click to Bookmark")
        dialog.geometry("600x400")
        dialog.transient(self)
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (600 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Find all questions
        questions = []
        search_start = "1.0"
        while True:
            pos = self.response_box.search("QUESTION:", search_start, stopindex=tk.END)
            if not pos:
                break
            
            line_num = pos.split('.')[0]
            line_end = f"{line_num}.end"
            q_text = self.response_box.get(pos, line_end).strip()
            
            # Check if already bookmarked
            is_bookmarked = any(idx.split('.')[0] == line_num for idx, _ in self.bookmarks)
            
            questions.append((pos, q_text, is_bookmarked))
            search_start = f"{int(line_num) + 1}.0"
        
        if not questions:
            ttk.Label(dialog, text="No questions found in chat", font=('Arial', 12)).pack(pady=20)
            return
        
        # Header
        ttk.Label(dialog, text=f"Found {len(questions)} questions. Click to bookmark:", font=('Arial', 11, 'bold')).pack(pady=5)
        
        # Scrollable list
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling (macOS compatible)
        def _on_mousewheel(event):
            # macOS uses smaller delta values, Windows uses 120/-120
            if event.delta:
                # Normalize scroll direction
                scroll_amount = -1 if event.delta > 0 else 1
                canvas.yview_scroll(scroll_amount, "units")
        
        # Bind mouse wheel to canvas and dialog
        canvas.bind("<MouseWheel>", _on_mousewheel)
        dialog.bind("<MouseWheel>", _on_mousewheel)
        # Also bind to scrollable_frame for when mouse is over items
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Add each question
        for i, (pos, q_text, is_bookmarked) in enumerate(questions):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", pady=2)
            
            # Bookmark indicator
            indicator = "🔖" if is_bookmarked else "○"
            
            btn = ttk.Button(
                frame, 
                text=f"{indicator} Q{i+1}: {q_text[:60]}{'...' if len(q_text) > 60 else ''}", 
                command=lambda p=pos, t=q_text[:40]: self._bookmark_and_jump(p, t, dialog)
            )
            btn.pack(fill="x")
            
            # Bind mousewheel to each frame and button for scrolling
            frame.bind("<MouseWheel>", _on_mousewheel)
            btn.bind("<MouseWheel>", _on_mousewheel)
        
        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def _bookmark_and_jump(self, pos: str, text: str, dialog=None):
        """Bookmark a question and jump to it."""
        # Add bookmark if not exists
        line_num = pos.split('.')[0]
        is_bookmarked = any(idx.split('.')[0] == line_num for idx, _ in self.bookmarks)
        
        if not is_bookmarked:
            self._add_bookmark(pos, f"QUESTION: {text}")
        
        # Jump to it
        self.response_box.see(pos)
        self._flash_bookmark(pos)
        
        if dialog:
            dialog.destroy()

    def toggle_optimization_mode(self):
        """
        Toggle Fast Mode (optimization) on/off.
        
        ON (default): Faster responses, compresses images, summarizes old chat
        OFF: Full context sent every time (slower but 100% complete)
        
        Your full chat history is ALWAYS preserved locally either way!
        """
        self.assistant.optimization_mode = not self.assistant.optimization_mode
        
        if self.assistant.optimization_mode:
            self.optimize_btn.config(text="⚡ Fast")
            self.status.config(text="⚡ Fast Mode ON - Optimized for speed")
        else:
            self.optimize_btn.config(text="🐢 Full")
            self.status.config(text="🐢 Full Mode - Sending complete context (slower)")

    # ============================================================================
    # BALANCE / BILLING MANAGEMENT
    # ============================================================================
    # DRAG AND DROP REORDERING
    # ============================================================================
    
    def _setup_drag_drop(self, tree: ttk.Treeview, tree_type: str):
        """
        Set up drag-and-drop reordering for a Treeview.
        tree_type: "tabs" or "chats"
        """
        tree._drag_data = {"item": None, "tree_type": tree_type}
        
        tree.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, tree))
        tree.bind("<B1-Motion>", lambda e: self._on_drag_motion(e, tree))
        tree.bind("<ButtonRelease-1>", lambda e: self._on_drag_release(e, tree))
    
    def _on_drag_start(self, event, tree: ttk.Treeview):
        """Start dragging an item."""
        item = tree.identify_row(event.y)
        if item:
            tree._drag_data["item"] = item
            tree._drag_data["start_y"] = event.y
            tree._drag_data["is_dragging"] = False  # Will be set to True if actually dragged
    
    def _on_drag_motion(self, event, tree: ttk.Treeview):
        """Show visual feedback while dragging."""
        if not tree._drag_data["item"]:
            return
        
        # Check if mouse has moved enough to be considered a drag (not just a click)
        start_y = tree._drag_data.get("start_y", event.y)
        if abs(event.y - start_y) > 5:  # 5 pixel threshold
            tree._drag_data["is_dragging"] = True
            tree.config(cursor="hand2")
    
    def _on_drag_release(self, event, tree: ttk.Treeview):
        """Drop the item at new position."""
        tree.config(cursor="")  # Reset cursor
        
        if not tree._drag_data["item"]:
            return
        
        dragged_item = tree._drag_data["item"]
        target_item = tree.identify_row(event.y)
        was_dragging = tree._drag_data.get("is_dragging", False)
        
        # Reset drag data
        tree._drag_data["item"] = None
        tree._drag_data["is_dragging"] = False
        
        # Only reorder if actually dragged (not just clicked)
        if not was_dragging:
            return
        
        if not target_item or target_item == dragged_item:
            return
        
        tree_type = tree._drag_data["tree_type"]
        
        if tree_type == "tabs":
            self._reorder_tabs(tree, dragged_item, target_item)
        elif tree_type == "chats":
            self._reorder_chats(tree, dragged_item, target_item)
    
    def _reorder_tabs(self, tree: ttk.Treeview, dragged: str, target: str):
        """Reorder tabs or subtabs."""
        try:
            # Determine if we're moving a tab or subtab
            dragged_is_tab = dragged.startswith("tab_")
            target_is_tab = target.startswith("tab_")
            
            if dragged_is_tab and target_is_tab:
                # Moving a tab to another tab position
                dragged_idx = int(dragged.split("_")[1])
                target_idx = int(target.split("_")[1])
                
                # Reorder in data
                tabs = self.prompt_manager.data["tabs"]
                if 0 <= dragged_idx < len(tabs) and 0 <= target_idx < len(tabs):
                    item = tabs.pop(dragged_idx)
                    tabs.insert(target_idx, item)
                    self.prompt_manager.save_tabs()
                    self.load_tabs()
                    self.status.config(text=f"📋 Moved tab to position {target_idx + 1}")
            
            elif dragged.startswith("sub_") and target.startswith("sub_"):
                # Moving a subtab within the same parent
                dragged_parts = dragged.split("_")
                target_parts = target.split("_")
                
                dragged_tab_idx = int(dragged_parts[1])
                dragged_sub_idx = int(dragged_parts[2])
                target_tab_idx = int(target_parts[1])
                target_sub_idx = int(target_parts[2])
                
                # Only allow reordering within the same tab
                if dragged_tab_idx == target_tab_idx:
                    subtabs = self.prompt_manager.data["tabs"][dragged_tab_idx]["subTabs"]
                    if 0 <= dragged_sub_idx < len(subtabs) and 0 <= target_sub_idx < len(subtabs):
                        item = subtabs.pop(dragged_sub_idx)
                        subtabs.insert(target_sub_idx, item)
                        self.prompt_manager.save_tabs()
                        self.load_tabs()
                        self.status.config(text=f"📋 Moved subtab to position {target_sub_idx + 1}")
                else:
                    self.status.config(text="⚠️ Can only reorder subtabs within same tab")
            
            elif dragged.startswith("sub_") and target_is_tab:
                # Moving subtab to a different tab
                dragged_parts = dragged.split("_")
                dragged_tab_idx = int(dragged_parts[1])
                dragged_sub_idx = int(dragged_parts[2])
                target_tab_idx = int(target.split("_")[1])
                
                if dragged_tab_idx != target_tab_idx:
                    source_subtabs = self.prompt_manager.data["tabs"][dragged_tab_idx]["subTabs"]
                    target_subtabs = self.prompt_manager.data["tabs"][target_tab_idx]["subTabs"]
                    
                    if 0 <= dragged_sub_idx < len(source_subtabs):
                        item = source_subtabs.pop(dragged_sub_idx)
                        target_subtabs.append(item)
                        self.prompt_manager.save_tabs()
                        self.load_tabs()
                        self.status.config(text=f"📋 Moved subtab to tab '{self.prompt_manager.get_tab_name(target_tab_idx)}'")
                        
        except Exception as e:
            print(f"Tab reorder error: {e}")
            self.status.config(text=f"❌ Reorder failed: {e}")
    
    def _reorder_chats(self, tree: ttk.Treeview, dragged: str, target: str):
        """Reorder chat sessions."""
        try:
            if not dragged.startswith("chat_") or not target.startswith("chat_"):
                return
            
            dragged_idx = int(dragged.split("_")[1])
            target_idx = int(target.split("_")[1])
            
            sessions = self.chat_manager.sessions
            if 0 <= dragged_idx < len(sessions) and 0 <= target_idx < len(sessions):
                item = sessions.pop(dragged_idx)
                sessions.insert(target_idx, item)
                self.chat_manager.save()
                self.load_chat_tabs()
                
                # Re-select the moved item
                new_id = f"chat_{target_idx}"
                if tree.exists(new_id):
                    tree.selection_set(new_id)
                    tree.see(new_id)
                
                self.status.config(text=f"💬 Moved chat to position {target_idx + 1}")
                
        except Exception as e:
            print(f"Chat reorder error: {e}")
            self.status.config(text=f"❌ Reorder failed: {e}")

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    
    def _restart_self():
        """
        Relaunch the current script using the same Python interpreter and args,
        then terminate this process (after closing Tk and the hotkey listener).
        """
        try:
            # Spawn the new process first
            python = sys.executable
            script = os.path.abspath(sys.argv[0])
            args = [python, script] + sys.argv[1:]
            subprocess.Popen(args)
        except Exception as e:
            print(f"❌ Restart spawn failed: {e}")
            return

        # Try to persist UI prefs before exit (optional but nice)
        try:
            app.save_ui_prefs()
        except Exception:
            pass

        # Stop listener if present
        try:
            listener.stop()
        except Exception:
            pass

        # Destroy Tk and hard-exit (to kill worker threads cleanly)
        try:
            app.destroy()
        except Exception:
            pass
        os._exit(0)


    # Define this AFTER app is created
    def setup_hotkey_listener():
        from pynput import keyboard
        combo_upload_resume = {keyboard.KeyCode(char='2'), keyboard.KeyCode(char='3')}
        combo_focus_chatbox = {keyboard.KeyCode(char='1'), keyboard.KeyCode(char='2')}
        combo_toggle_input_mode = {keyboard.KeyCode(char='3'), keyboard.KeyCode(char='4')}
        combo_listen_external = {keyboard.KeyCode(char='5'), keyboard.KeyCode(char='6')}
        combo_increase_font = {keyboard.Key.cmd,keyboard.Key.ctrl,  keyboard.KeyCode(char='=')}   # Cmd + +
        combo_decrease_font = {keyboard.Key.cmd, keyboard.Key.ctrl, keyboard.KeyCode(char='-')}   # Cmd + -
        combo_pin_window     = {keyboard.Key.cmd, keyboard.KeyCode(char='p')}  # Cmd + P
        combo_restart = {keyboard.Key.cmd, keyboard.Key.shift, keyboard.KeyCode(char='z')}





        current_keys = set()
        
        def on_activate_toggle_input():
            print("🎚 Global hotkey 3 + 4: Toggle input device (internal/external)")
            app.focus_force()
            app.lift()
            app.attributes('-topmost', True)
            app.attributes('-topmost', False)
            app.toggle_input_mode()

            
        def on_activate_upload_resume():
            print("📁 Global hotkey 2 + 3: Trigger resume upload")
            app.focus_force()
            app.lift()
            app.attributes('-topmost', True)
            app.attributes('-topmost', False)
            app.upload_resume()

        def on_activate_focus_chatbox():
            print("⌨️ Global hotkey 1 + 2: Focus chat input")
            app.focus_force()
            app.lift()
            app.attributes('-topmost', True)
            app.attributes('-topmost', False)
            app.input_entry.focus_set()
            app.input_entry.icursor(tk.END)

        def on_press(key):
            if key not in combo_listen_external:
                hotkey_listen.press(listener.canonical(key))

            hotkey_stop.press(listener.canonical(key))
            hotkey_screenshot.press(listener.canonical(key))

            if key in (combo_focus_chatbox | combo_upload_resume | combo_toggle_input_mode |
                    combo_listen_external | combo_increase_font | combo_decrease_font |
                    combo_pin_window | combo_restart):
                current_keys.add(key)

                if combo_focus_chatbox.issubset(current_keys):
                    on_activate_focus_chatbox()
                elif combo_upload_resume.issubset(current_keys):
                    on_activate_upload_resume()
                elif combo_toggle_input_mode.issubset(current_keys):
                    on_activate_toggle_input()
                elif combo_listen_external.issubset(current_keys):
                    on_activate_listen_external()
                elif combo_increase_font.issubset(current_keys):
                    print("🔎 Global hotkey Cmd + +: Increase font")
                    app.increase_font()
                elif combo_decrease_font.issubset(current_keys):
                    print("🔍 Global hotkey Cmd -: Decrease font")
                    app.decrease_font()
                elif combo_pin_window.issubset(current_keys):
                    print("📌 Global hotkey Cmd + P: Toggle pin")
                    app.toggle_always_on_top()
                elif combo_restart.issubset(current_keys):
                    on_activate_restart()


                        

            
        def on_activate_restart():
            print("🔁 Global hotkey Cmd + R: Restarting app...")
            # Do it on a short timer so the print/status can flush
            try:
                app.status.config(text="🔁 Restarting...")
            except Exception:
                pass
            threading.Thread(target=_restart_self, daemon=True).start()

                    
        def on_activate_listen_external():
            if not app.assistant.recorder.is_recording:
                print("🎧 Global hotkey 5 + 6: Start Listening with External Mic")
                app.assistant.recorder.input_mode = "external"
                app.toggle_recording()
            else:
                print("🛑 Global hotkey 5 + 6: Stop and Process (External Mic)")
                app.toggle_recording()

                # Schedule switch back to BlackHole after recording is done
                def revert_input_mode():
                    time.sleep(1.5)  # slight delay to ensure stop finishes
                    app.assistant.recorder.input_mode = "internal"
                    app.status.config(text="🔈 Reverted to Internal Audio (BlackHole) after external session")
                    app.toggle_input_btn.config(text="🔈 Internal Audio (BlackHole)")

                threading.Thread(target=revert_input_mode, daemon=True).start()




            
            
            

        def on_release(key):
            hotkey_listen.release(listener.canonical(key))
            hotkey_stop.release(listener.canonical(key))
            hotkey_screenshot.release(listener.canonical(key))
            current_keys.discard(key)

        def on_activate_listen():
            if not app.assistant.recorder.is_recording:
                print("🎤 Global hotkey `: Start Listening")
                app.toggle_recording()
            else:
                print("🛑 Global hotkey `: Stop & Process")
                app.toggle_recording()

        def on_activate_stop():
            """Stop GPT generation and reset any processing flags."""
            print("🧠 Global hotkey ~: Force stop and reset state.")
            app.stop_output()
            app.is_processing_audio = False            # ✅ Reset processing state
            app.assistant.streaming = False            # ✅ Ensure streaming is stopped
            app.assistant.current_response = ""        # ✅ Clear any lingering response
            app.record_btn.config(text="🎤 Listen", state=tk.NORMAL)  # ✅ Reset button state
            app.stop_btn.config(state=tk.DISABLED)     # ✅ Ensure stop button is disabled
            app.status.config(text="✅ Stopped and Reset. Ready for next input.")


        def on_activate_screenshot():
            print("📸 Global hotkey !: Capturing full monitor under mouse and attaching...")
            try:
                mouse_x, mouse_y = pyautogui.position()
                screens = Quartz.NSScreen.screens()
                target_screen = None

                for screen in screens:
                    frame = screen.frame()
                    x = int(frame.origin.x)
                    y = int(frame.origin.y)
                    width = int(frame.size.width)
                    height = int(frame.size.height)

                    if x <= mouse_x < x + width and y <= mouse_y < y + height:
                        target_screen = (x, y, width, height)
                        break

                if not target_screen:
                    app.status.config(text="❌ No monitor found under mouse")
                    return

                screenshot = pyautogui.screenshot(region=target_screen)
                
                # Compress for faster transmission
                b64_image = compress_image_png(screenshot, max_size=1280)
                compressed_size = len(b64_image) // 1024
                print(f"📸 Screenshot compressed: {compressed_size}KB")

                if not hasattr(app, 'pending_attachments'):
                    app.pending_attachments = []

                app.pending_attachments.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                })

                app.status.config(text=f"📎 Screenshot attached ({compressed_size}KB). Press Enter to send.")
                app.input_entry.insert(tk.END, "📎 [Full screen screenshot ready to send] ")

            except Exception as e:
                app.status.config(text=f"❌ Screenshot error: {e}")
                print(f"❌ Screenshot error: {e}")

        hotkey_listen = keyboard.HotKey(keyboard.HotKey.parse('`'), on_activate_listen)
        hotkey_stop = keyboard.HotKey(keyboard.HotKey.parse('~'), on_activate_stop)
        hotkey_screenshot = keyboard.HotKey(keyboard.HotKey.parse('!'), on_activate_screenshot)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        return listener


    listener = setup_hotkey_listener()
    listener.start()

    app.mainloop()
    listener.join()

