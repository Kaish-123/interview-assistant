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

from pynput import keyboard
import Quartz
import Quartz
import pyautogui

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
window = get_window_under_mouse()
if window:
    print(f"Window under mouse: {window.get('kCGWindowName', 'No Title')}")


def get_window_list():
    window_list = []
    window_info_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for window_info in window_info_list:
        window_list.append(window_info)
    return window_list

# Example usage:
windows = get_window_list()
for window in windows:
    print(window.get('kCGWindowName', 'No Title'))


def on_activate():
    if not app.assistant.recorder.is_recording:
        print("🎤 Global hotkey: Start Listening")
        app.toggle_recording()
    else:
        print("🛑 Global hotkey: Stop & Process")
        app.toggle_recording()






# Configuration
API_KEY = "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"
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
        self.messages = [{"role": "system", "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."}]
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12

    def load_resume(self, file_path):
        try:
            text = textract.process(file_path).decode('utf-8')
            self.messages.append({"role": "system", "content": f"Use this resume content to contextualize answers: {text}"})
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

    def stream_gpt_response(self, text_widget, status_label, button):
        with self.lock:
            self.current_response = ""
            self.streaming = True

            # Placeholder added to messages (no slicing now)
            placeholder = {"role": "assistant", "content": ""}
            self.messages.append(placeholder)

            try:
                # Use full message history as-is
                stream = client.chat.completions.create(
                    #model="gpt-3.5-turbo",
                    #model="gpt-4-turbo",
                    model="gpt-4o",
                    messages=self.messages,
                    stream=True
                )

                buffer = ""
                last_update = time.time()

                # Show "Answer:" in chat box
                text_widget.config(state=tk.NORMAL)
                text_widget.insert(tk.END, "Answer: ")
                text_widget.config(state=tk.DISABLED)
                text_widget.see(tk.END)

                for chunk in stream:
                    if not self.streaming:
                        break

                    delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
                    if delta:
                        buffer += delta
                        self.current_response += delta
                        placeholder["content"] = self.current_response

                        if time.time() - last_update > 0.05 or len(buffer) > 20:
                            self.update_text_widget(text_widget, buffer)
                            buffer = ""
                            last_update = time.time()

                if buffer:
                    self.update_text_widget(text_widget, buffer)

            except Exception as e:
                placeholder["content"] = f"❌ GPT Error: {str(e)}"
                self.update_text_widget(text_widget, f"\n{placeholder['content']}\n")

            finally:
                self.streaming = False
                button.config(state=tk.NORMAL)
                status_label.config(text="✅ Ready")







    def update_text_widget(self, text_widget, new_text_part: str):
        # Enable the text widget for editing
        text_widget.config(state=tk.NORMAL)

        # Append only the new part of the message (delta)
        text_widget.insert(tk.END, new_text_part)

        # Auto-scroll if the user is already at the bottom
        bottom_visible = text_widget.yview()[1] >= 0.99
        if bottom_visible:
            text_widget.see(tk.END)

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
class SidebarFrame(tk.Frame):
    def __init__(self, master, assistant, **kwargs):
        super().__init__(master, bg='#202123', **kwargs)
        self.assistant = assistant
        self.tabs = {}

        self.tab_listbox = tk.Listbox(self, width=20, bg='#202123', fg='white')
        self.tab_listbox.pack(side="top", fill="both", expand=False)
        self.tab_listbox.bind('<<ListboxSelect>>', self.on_tab_select)

        self.subtab_listbox = tk.Listbox(self, width=20, bg='#2A2B2D', fg='white')
        self.subtab_listbox.pack(side="top", fill="both", expand=True)
        self.subtab_listbox.bind('<<ListboxSelect>>', self.on_subtab_select)

        self.prompt_editor = tk.Text(self, height=5, wrap='word', bg='#343541', fg='white')
        self.prompt_editor.pack(fill="x", padx=5, pady=(5, 0))

        btns = tk.Frame(self, bg='#202123')
        btns.pack(fill="x")
        tk.Button(btns, text="Add Tab", command=self.add_tab).pack(side="left", padx=2)
        tk.Button(btns, text="Add Subtab", command=self.add_subtab).pack(side="left", padx=2)
        tk.Button(btns, text="Save Prompt", command=self.save_prompt).pack(side="left", padx=2)

    def add_tab(self):
        name = f"Tab {len(self.tabs) + 1}"
        self.tabs[name] = {}
        self.tab_listbox.insert(tk.END, name)

    def add_subtab(self):
        tab = self.get_selected_tab()
        if not tab: return
        subname = f"Subtab {len(self.tabs[tab]) + 1}"
        self.tabs[tab][subname] = ""
        self.subtab_listbox.insert(tk.END, subname)

    def get_selected_tab(self):
        selected = self.tab_listbox.curselection()
        return self.tab_listbox.get(selected[0]) if selected else None

    def get_selected_subtab(self):
        selected = self.subtab_listbox.curselection()
        return self.subtab_listbox.get(selected[0]) if selected else None

    def on_tab_select(self, event):
        tab = self.get_selected_tab()
        if tab:
            self.subtab_listbox.delete(0, tk.END)
            for sub in self.tabs[tab]:
                self.subtab_listbox.insert(tk.END, sub)

    def on_subtab_select(self, event):
        tab = self.get_selected_tab()
        subtab = self.get_selected_subtab()
        if tab and subtab:
            self.prompt_editor.delete("1.0", tk.END)
            self.prompt_editor.insert(tk.END, self.tabs[tab][subtab])

            # Push this as active system prompt
            content = self.tabs[tab][subtab].strip()
            if content:
                self.assistant.messages.append({"role": "system", "content": content})
                print(f"🧠 Loaded system prompt from [{tab} > {subtab}]")

    def save_prompt(self):
        tab = self.get_selected_tab()
        subtab = self.get_selected_subtab()
        if tab and subtab:
            self.tabs[tab][subtab] = self.prompt_editor.get("1.0", tk.END).strip()


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interview Assistant")
        self.geometry("800x600")
        self.configure(bg='#343541')
        self.always_on_top = False

        self.toggle_lock = threading.Lock()
        self.is_processing_audio = False

        self.assistant = ChatGPTAssistant()
        self.setup_ui()
        self.bind_all("<Command-v>", self.handle_paste)


        
    def handle_paste(self, event=None):
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

                # Store it temporarily for the next message
                if not hasattr(self, 'pending_attachments'):
                    self.pending_attachments = []
                self.pending_attachments.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                })

                print("📎 Image attachment ready")
                self.status.config(text="📎 Image ready to send. Press Enter.")
                self.input_entry.insert(tk.END, "📎 [Image attachment ready] ")
            else:
                text = pyperclip.paste()
                if text.strip():
                    print("📋 Text pasted")
                    self.input_entry.insert(tk.END, text.strip())
        except Exception as e:
            print(f"❌ Paste failed: {e}")
            self.status.config(text=f"❌ Paste error: {e}")




    def setup_ui(self):
        self.status = ttk.Label(self, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=5, anchor="w", padx=10)
        
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # Sidebar for prompts
        self.sidebar = SidebarFrame(container, self.assistant)
        self.sidebar.pack(side="left", fill="y")

        text_frame = ttk.Frame(container)
        text_frame.pack(side="right", fill="both", expand=True)


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

        # Button bar above chat entry
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

        # Chat input bar at bottom
        input_frame = ttk.Frame(self)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 14), width=80)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))

        self.input_entry.bind("<Return>", lambda event: self.submit_text_question())

        self.submit_btn = ttk.Button(input_frame, text="➡️", width=4, command=self.submit_text_question)
        self.submit_btn.pack(side="right")


    def submit_text_question(self):
        question = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)

        if not question and not hasattr(self, 'pending_attachments'):
            return

        if question == "--":
            self.capture_and_submit_screenshot()
            return

        content = []
        if question and not question.startswith("📎"):
            content.append({"type": "text", "text": question})

        if hasattr(self, 'pending_attachments'):
            content.extend(self.pending_attachments)
            del self.pending_attachments

        # Flatten for GPT and display
        flat_text = "\n".join(
            c["text"] if c["type"] == "text" else "[Image]" for c in content
        )

        # ✅ Insert question only once
        self.response_box.config(state=tk.NORMAL)
        self.response_box.insert(tk.END, f"\n\nQuestion: {flat_text.strip()}\n")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.see(tk.END)

        self.assistant.messages.append({"role": "user", "content": flat_text})

        self.status.config(text="💡 Generating answer...")
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(self.response_box, self.status, self.record_btn),
            daemon=True
        ).start()

            
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
                print("⏳ Already processing. Please wait.")
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
            question = self.assistant.transcribe_audio(filename)

            if question.startswith("❌"):
                self.status.config(text=question)
                return

            # === Maintain consistent format with typed input ===
            content = [{"type": "text", "text": question}]

            # Flatten input for GPT model
            flat_text = "\n".join(
                c["text"] if c["type"] == "text" else "[Image]" for c in content
            )

            # Show question in UI
            self.response_box.config(state=tk.NORMAL)
            self.response_box.insert(tk.END, f"\n\nQuestion: {flat_text.strip()}\n")
            self.response_box.config(state=tk.DISABLED)
            self.response_box.see(tk.END)

            # Append flat question for GPT context
            self.assistant.messages.append({"role": "user", "content": flat_text})

            self.status.config(text="💡 Generating answer...")
            threading.Thread(
                target=self.assistant.stream_gpt_response,
                args=(self.response_box, self.status, self.record_btn),
                daemon=True
            ).start()

        finally:
            self.is_processing_audio = False





    def start_new_chat(self):
        self.assistant.messages = [{"role": "system", "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."}]
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

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))

    # Define this AFTER app is created
    def setup_hotkey_listener():
        def on_activate_listen():
            if not app.assistant.recorder.is_recording:
                print("🎤 Global hotkey `: Start Listening")
                app.toggle_recording()
            else:
                print("🛑 Global hotkey `: Stop & Process")
                app.toggle_recording()

        def on_activate_stop():
            print("🧠 Global hotkey ~: Stop generating answer")
            app.stop_output()

        import pygetwindow as gw

        import Quartz

        def on_activate_screenshot():
            print("📸 Global hotkey !: Capturing active window under mouse and attaching...")
            try:
                # Get mouse position
                mouse_x, mouse_y = pyautogui.position()

                # Get list of all on-screen windows
                window_info_list = Quartz.CGWindowListCopyWindowInfo(
                    Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)

                # Find the window under the mouse cursor
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
                    print("❌ No window found under mouse cursor")
                    return

                # Screenshot only the window region
                region = (
                    int(target_window['X']),
                    int(target_window['Y']),
                    int(target_window['Width']),
                    int(target_window['Height'])
                )
                screenshot = pyautogui.screenshot(region=region)

                buffer = io.BytesIO()
                screenshot.save(buffer, format="PNG")
                buffer.seek(0)
                b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

                if not hasattr(app, 'pending_attachments'):
                    app.pending_attachments = []

                app.pending_attachments.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"}
                })

                app.status.config(text="📎 Screenshot of active window attached. Press Enter to send.")
                app.input_entry.insert(tk.END, "📎 [Screenshot ready to send] ")

            except Exception as e:
                app.status.config(text=f"❌ Screenshot capture failed: {e}")
                print(f"❌ Screenshot error: {e}")



        hotkey_listen = keyboard.HotKey(keyboard.HotKey.parse('`'), on_activate_listen)
        hotkey_stop = keyboard.HotKey(keyboard.HotKey.parse('~'), on_activate_stop)
        hotkey_screenshot = keyboard.HotKey(keyboard.HotKey.parse('!'), on_activate_screenshot)

        def on_press(key):
            hotkey_listen.press(listener.canonical(key))
            hotkey_stop.press(listener.canonical(key))
            hotkey_screenshot.press(listener.canonical(key))

        def on_release(key):
            hotkey_listen.release(listener.canonical(key))
            hotkey_stop.release(listener.canonical(key))
            hotkey_screenshot.release(listener.canonical(key))

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        return listener

    listener = setup_hotkey_listener()
    listener.start()

    app.mainloop()
    listener.join()



