import sounddevice as sd
import numpy as np
import wave
import threading
from openai import OpenAI
import tkinter as tk
from tkinter import ttk, filedialog
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
import Quartz
import os
import json

# Configuration
API_KEY = "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"
 # Replace with your actual API key
client = OpenAI(api_key=API_KEY)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
CHUNK = 1024
BLACKHOLE_DEVICE = "BlackHole"
CHAT_HISTORY_FILE = "./chat_logs/chat_history.json"

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.audio_queue = queue.Queue()

    def find_blackhole_device(self):
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if BLACKHOLE_DEVICE in device['name']:
                return i
        raise ValueError("BlackHole device not found")

    def start_recording(self):
        device_id = self.find_blackhole_device()
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
        threading.Thread(target=self.process_audio, daemon=True).start()

    def process_audio(self):
        while self.is_recording or not self.audio_queue.empty():
            try:
                self.frames.append(self.audio_queue.get(timeout=0.1))
            except queue.Empty:
                continue

    def stop_recording(self, filename="interviewer.wav"):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

        if self.frames:
            audio_data = np.concatenate(self.frames)
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())
        return filename

class ChatGPTAssistant:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.streaming = False
        self.current_response = ""
        self.font_size = 12
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.displayed_messages_count = 0
        self.messages = self.load_chat_history() or [{
            "role": "system", 
            "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."
        }]
    
    def save_chat_history(self):
        os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def load_chat_history(self):
        if not os.path.exists(CHAT_HISTORY_FILE):
            return None
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def load_resume(self, file_path):
        try:
            text = textract.process(file_path).decode('utf-8')
            self.messages.append({
                "role": "system", 
                "content": f"Use this resume content to contextualize answers: {text}"
            })
            return True, "📄 Resume uploaded and processed successfully."
        except Exception as e:
            return False, f"❌ Error processing resume: {str(e)}"

    def transcribe_audio(self, filename):
        try:
            with open(filename, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcription.text
        except Exception as e:
            return f"❌ Transcription error: {str(e)}"

    def stream_gpt_response(self, app):
        with self.lock:
            self.current_response = ""
            self.streaming = True

            # Insert a placeholder in messages list
            placeholder = {"role": "assistant", "content": ""}
            self.messages.append(placeholder)

            try:
                stream = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=self.messages[:-1],  # exclude placeholder from context
                    stream=True
                )

                buffer = ""
                last_update = time.time()

                for chunk in stream:
                    if not self.streaming:
                        break

                    delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
                    if delta:
                        buffer += delta
                        self.current_response += delta
                        placeholder["content"] = self.current_response

                        # Throttle UI updates
                        if time.time() - last_update > 0.05 or len(buffer) > 20:
                            app.after(0, app.update_text_widget)
                            buffer = ""
                            last_update = time.time()

                # Final update
                if buffer:
                    app.after(0, app.update_text_widget)

            except Exception as e:
                placeholder["content"] = f"❌ GPT Error: {str(e)}"
                app.after(0, app.update_text_widget)

            finally:
                self.streaming = False
                app.record_btn.config(state=tk.NORMAL)
                app.status.config(text="✅ Ready")
                self.save_chat_history()
                app.after(0, app.update_text_widget)

    def format_message_content(self, content):
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if part["type"] == "text":
                    text_parts.append(part["text"])
                elif part["type"] == "image_url":
                    text_parts.append("📎 [Image]")
            return " ".join(text_parts)
        return content

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

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interview Assistant")
        self.geometry("800x600")
        self.configure(bg='#343541')
        self.always_on_top = False

        self.toggle_lock = threading.Lock()
        self.is_processing_audio = False
        self.last_scroll_position = 0
        self.streaming_start_index = None
        self.displayed_messages_count = 0

        self.assistant = ChatGPTAssistant()
        self.setup_ui()
        self.restore_chat_history()
        self.bind_all("<Command-v>", self.handle_paste)

    def restore_chat_history(self):
        if self.assistant.messages:
            self.response_box.config(state=tk.NORMAL)
            self.response_box.delete(1.0, tk.END)
            
            # Skip system messages
            for msg in self.assistant.messages:
                if msg["role"] == "system":
                    continue
                prefix = "Question: " if msg["role"] == "user" else "Answer: "
                content = self.assistant.format_message_content(msg["content"])
                self.response_box.insert(tk.END, f"{prefix}{content}\n\n")
                self.displayed_messages_count += 1
            
            self.response_box.config(state=tk.DISABLED)
            self.response_box.see(tk.END)

    def setup_ui(self):
        self.status = ttk.Label(self, text="🔊 Ready")
        self.status.pack(pady=5, anchor="w", padx=10)

        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True, padx=10)

        self.response_box = tk.Text(
            text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
            bg='#343541', fg='white', insertbackground='white',
            selectbackground='#4E4E4E', highlightthickness=0
        )
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.insert(tk.END, "🤖 Start a new conversation or ask your first question...")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.tag_configure('code', foreground='#4EC9B0')

        scrollbar = ttk.Scrollbar(text_frame, command=self.response_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.response_box.config(yscrollcommand=scrollbar.set)

        # Capture scroll position
        self.response_box.bind("<MouseWheel>", self.capture_scroll_position)
        self.response_box.bind("<Button-4>", self.capture_scroll_position)
        self.response_box.bind("<Button-5>", self.capture_scroll_position)

        # Button bar
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.record_btn = ttk.Button(control_frame, text="🎤 Listen", command=self.toggle_recording)
        self.record_btn.pack(side="left", padx=4)

        self.new_chat_btn = ttk.Button(control_frame, text="🆕 New", command=self.start_new_chat)
        self.new_chat_btn.pack(side="left", padx=4)

        self.stop_btn = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_output, state=tk.DISABLED)
        self.stop_btn.pack(side="left", padx=4)

        self.upload_btn = ttk.Button(control_frame, text="📁 Resume", command=self.upload_resume)
        self.upload_btn.pack(side="left", padx=4)

        font_controls = ttk.Frame(control_frame)
        font_controls.pack(side="left", padx=10)
        ttk.Button(font_controls, text="A+", command=self.increase_font).pack(side="left")
        ttk.Button(font_controls, text="A-", command=self.decrease_font).pack(side="left")

        self.topmost_btn = ttk.Button(control_frame, text="📌 Pin", command=self.toggle_always_on_top)
        self.topmost_btn.pack(side="right", padx=4)

        # Input area
        input_frame = ttk.Frame(self)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 14), width=80)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
        self.input_entry.bind("<Return>", lambda event: self.submit_text_question())

        self.submit_btn = ttk.Button(input_frame, text="➡️", width=4, command=self.submit_text_question)
        self.submit_btn.pack(side="right")

    def capture_scroll_position(self, event=None):
        if self.response_box.yview()[1] < 0.99:  # Not at bottom
            self.last_scroll_position = self.response_box.yview()[0]
        else:
            self.last_scroll_position = 1.0  # At bottom

    def update_text_widget(self):
        self.response_box.config(state=tk.NORMAL)
        
        # Capture scroll position before update
        self.capture_scroll_position()
        
        # Display new complete messages
        end_index = len(self.assistant.messages)
        if self.assistant.streaming:
            end_index -= 1  # Skip the streaming message
        
        for i in range(self.displayed_messages_count, end_index):
            msg = self.assistant.messages[i]
            if msg['role'] == 'system':
                continue
                
            prefix = "Question: " if msg['role'] == 'user' else "Answer: "
            content = self.assistant.format_message_content(msg['content'])
            self.response_box.insert(tk.END, f"{prefix}{content}\n\n")
            self.displayed_messages_count += 1
        
        # Handle streaming message
        if self.assistant.streaming:
            if not self.streaming_start_index:
                self.response_box.insert(tk.END, "Answer: ")
                self.streaming_start_index = self.response_box.index(tk.END)
                self.response_box.insert(tk.END, self.assistant.current_response)
            else:
                # Update streaming text
                self.response_box.delete(self.streaming_start_index, tk.END)
                self.response_box.insert(self.streaming_start_index, self.assistant.current_response)
        elif self.streaming_start_index:
            # Streaming finished
            self.streaming_start_index = None
        
        # Highlight code blocks
        self.highlight_code()
        
        # Restore scroll position
        if self.last_scroll_position == 1.0:
            self.response_box.see(tk.END)
        else:
            self.response_box.yview_moveto(self.last_scroll_position)
        
        self.response_box.config(state=tk.DISABLED)

    def highlight_code(self):
        content = self.response_box.get("1.0", tk.END)
        self.response_box.tag_remove('code', "1.0", tk.END)
        code_blocks = re.finditer(r'```.*?\n.*?```', content, re.DOTALL)
        for match in code_blocks:
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.response_box.tag_add('code', start, end)

    def handle_paste(self, event=None):
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

                if not hasattr(self, 'pending_attachments'):
                    self.pending_attachments = []
                self.pending_attachments.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                })

                self.status.config(text="📎 Image ready to send. Press Enter.")
                self.input_entry.insert(tk.END, "📎 [Image attachment ready] ")
        except Exception as e:
            self.status.config(text=f"❌ Paste error: {e}")

    def submit_text_question(self, event=None):
        question = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)

        if not question and not hasattr(self, 'pending_attachments'):
            return

        # Handle screen capture
        if question == "--":
            self.capture_and_submit_screenshot()
            return

        # Build content
        content = []
        if question and not question.startswith("📎"):
            content.append({"type": "text", "text": question})

        if hasattr(self, 'pending_attachments'):
            content.extend(self.pending_attachments)
            del self.pending_attachments

        self.assistant.messages.append({"role": "user", "content": content})
        self.assistant.save_chat_history()
        
        # Update UI immediately
        self.update_text_widget()
        self.status.config(text="💡 Generating answer...")
        
        # Start streaming in background
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(self,),
            daemon=True
        ).start()

    def capture_and_submit_screenshot(self):
        self.status.config(text="📸 Capturing screen...")
        screenshot = pyautogui.screenshot()
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)

        self.assistant.messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Please analyze this screenshot."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('latin1')}"
                }}
            ]
        })
        self.assistant.save_chat_history()
        
        # Update UI immediately
        self.update_text_widget()
        self.status.config(text="🧠 Analyzing screenshot...")
        
        # Start streaming in background
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(self,),
            daemon=True
        ).start()

    def upload_resume(self):
        file_path = filedialog.askopenfilename(
            title="Select Resume File", 
            filetypes=[("All Files", "*.*")]
        )
        if file_path:
            success, message = self.assistant.load_resume(file_path)
            self.status.config(text=message)

    def toggle_recording(self):
        with self.toggle_lock:
            if self.is_processing_audio:
                return

            if not self.assistant.recorder.is_recording:
                self.assistant.streaming = False
                self.response_box.config(state=tk.NORMAL)
                self.response_box.delete(1.0, tk.END)
                self.response_box.insert(tk.END, "Listening...")
                self.response_box.config(state=tk.DISABLED)
                self.assistant.recorder.start_recording()
                self.status.config(text="🎙 Listening to interviewer...")
                self.record_btn.config(text="🛑 Stop & Process")
                self.stop_btn.config(state=tk.DISABLED)
            else:
                self.is_processing_audio = True
                self.record_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.status.config(text="💭 Processing question...")
                threading.Thread(target=self.process_recording, daemon=True).start()

    def process_recording(self):
        try:
            filename = self.assistant.recorder.stop_recording()
            question = self.assistant.transcribe_audio(filename).strip()

            if question.startswith("❌") or len(question.strip()) < 3:
                self.status.config(text="❌ Invalid transcription. Please retry.")
                return

            self.assistant.messages.append({"role": "user", "content": question})
            self.assistant.save_chat_history()
            
            # Update UI immediately
            self.update_text_widget()
            self.status.config(text="💡 Generating answer...")
            
            # Start streaming in background
            threading.Thread(
                target=self.assistant.stream_gpt_response,
                args=(self,),
                daemon=True
            ).start()
        finally:
            self.is_processing_audio = False

    def start_new_chat(self):
        self.assistant.messages = [{
            "role": "system", 
            "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."
        }]
        self.assistant.save_chat_history()
        self.displayed_messages_count = 0
        self.streaming_start_index = None
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

def setup_hotkey_listener(app):
    def on_activate_listen():
        if not app.assistant.recorder.is_recording:
            app.toggle_recording()
        else:
            app.toggle_recording()

    def on_activate_stop():
        app.stop_output()

    def on_activate_screenshot():
        try:
            mouse_x, mouse_y = pyautogui.position()
            window_info_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
            
            target_window = None
            for window in window_info_list:
                bounds = window.get('kCGWindowBounds', {})
                x = bounds.get('X', 0)
                y = bounds.get('Y', 0)
                width = bounds.get('Width', 0)
                height = bounds.get('Height', 0)
                if (x <= mouse_x <= x + width) and (y <= mouse_y <= y + height):
                    target_window = bounds
                    break

            if not target_window:
                app.status.config(text="❌ No window found under mouse cursor")
                return

            region = (
                int(target_window['X']),
                int(target_window['Y']),
                int(target_window['Width']),
                int(target_window['Height']))
            screenshot = pyautogui.screenshot(region=region)

            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

            if not hasattr(app, 'pending_attachments'):
                app.pending_attachments = []
            app.pending_attachments.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_image}"}
            })

            app.status.config(text="📎 Screenshot attached. Press Enter.")
            app.input_entry.insert(tk.END, "📎 [Screenshot ready] ")
        except Exception as e:
            app.status.config(text=f"❌ Screenshot error: {e}")

    hotkey_listen = keyboard.HotKey(keyboard.HotKey.parse('`'), on_activate_listen)
    hotkey_stop = keyboard.HotKey(keyboard.HotKey.parse('~'), on_activate_stop)
    hotkey_screenshot = keyboard.HotKey(keyboard.HotKey.parse('!'), on_activate_screenshot)

    def on_press(key):
        try:
            hotkey_listen.press(listener.canonical(key))
            hotkey_stop.press(listener.canonical(key))
            hotkey_screenshot.press(listener.canonical(key))
        except AttributeError:
            pass

    def on_release(key):
        pass

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    return listener

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))

    listener = setup_hotkey_listener(app)
    listener.start()

    app.mainloop()
    listener.stop()