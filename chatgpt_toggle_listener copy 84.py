
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
import json
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
# ... other imports remain the same ...

    
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
        self.input_mode = "internal"  # internal = BlackHole, external = mic

    def find_device(self):
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if self.input_mode == "internal" and "BlackHole" in device['name']:
                return i
            elif self.input_mode == "external" and device['max_input_channels'] > 0 and "BlackHole" not in device['name']:
                return i
        raise ValueError("🎙 Desired input device not found")

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

class ChatHistoryManager:
    def __init__(self, file_path="chats.json"):
        self.file_path = file_path
        self.sessions = []  # Each item: {"title": str, "messages": List[dict]}
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    self.sessions = json.load(f)
            except:
                self.sessions = []

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.sessions, f, indent=2)

    def add_session(self, title, messages):
        self.sessions.append({"title": title, "messages": messages})
        self.save()

    def get_titles(self):
        return [s["title"] for s in self.sessions]

    def get_session(self, index):
        return self.sessions[index]["messages"] if 0 <= index < len(self.sessions) else []


class ChatGPTAssistant:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.streaming = False
        self.current_response = ""
        self.messages = [{"role": "system", "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."}]
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12
        self.stream_thread = None 
        
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
        self.cancel_streaming()  # 🔴 Cancel any ongoing output

        def run_stream():
            with self.lock:
                self.current_response = ""
                self.streaming = True
                placeholder = {"role": "assistant", "content": ""}
                self.messages.append(placeholder)

                try:
                    stream = client.chat.completions.create(
                        model="gpt-4o",
                        messages=self.messages,
                        stream=True
                    )

                    buffer = ""
                    last_update = time.time()

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

        self.stream_thread = threading.Thread(target=run_stream, daemon=True)
        self.stream_thread.start()





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


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.toggle_lock = threading.Lock() 
        self.is_processing_audio = False 
        self.assistant = ChatGPTAssistant()  
        self.prompt_manager = PromptManager()
        self.chat_manager = ChatHistoryManager()
        
        self.setup_ui()  # Ensure UI setup is done first
        self.bind_all("<Command-v>", self.handle_paste)
        self.sidebar_visible = True
        self.current_tab = -1
        self.current_subtab = -1
        self.always_on_top = False 
        
        # Load chat tabs after the UI is set up
        self.load_tabs()
    
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


        
    def on_chat_tab_select(self, event):
        selected = self.chat_tabs.selection()
        if selected:
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
            self.toggle_input_btn.config(text="🎧 External Mic")
            self.status.config(text="🎧 Switched to External Microphone")
        else:
            self.assistant.recorder.input_mode = "internal"
            self.toggle_input_btn.config(text="🔈 Internal Audio (BlackHole)")
            self.status.config(text="🔈 Switched to Internal Audio (BlackHole)")

    def display_chat_history(self):
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        for msg in self.assistant.messages:
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, list):  # for image or mixed content
                    text = "\n".join(c["text"] if c["type"] == "text" else "[Image]" for c in content)
                else:
                    text = content
                self.response_box.insert(tk.END, f"\n\nQuestion: {text.strip()}\n")
            elif msg["role"] == "assistant":
                self.response_box.insert(tk.END, f"Answer: {msg['content'].strip()}\n")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.see(tk.END)

    


    def setup_ui(self):
        # Create paned window for sidebar and main content
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        # Create sidebar frame
        self.sidebar = ttk.Frame(self.paned, width=200)
        self.paned.add(self.sidebar, weight=0)
        
        
        

        # Create toggle button
        self.toggle_btn = ttk.Button(self.sidebar, text="☰", width=2, command=self.toggle_sidebar)
        self.toggle_btn.pack(pady=5, fill="x")

        # Create tab management area
        self.tab_frame = ttk.Frame(self.sidebar)
        self.tab_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create tab treeview
        self.tab_tree = ttk.Treeview(self.tab_frame, show="tree", selectmode="browse")
        self.tab_tree.pack(fill="both", expand=True, side="left")
        self.tab_tree.bind("<<TreeviewSelect>>", self.on_tab_select)

        # Chat History Treeview (below prompt tabs)
        ttk.Label(self.sidebar, text="💬 Past Chats").pack(anchor="w", padx=5)
        self.chat_tabs = ttk.Treeview(self.sidebar, show="tree", selectmode="browse")
        self.chat_tabs.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        self.chat_tabs.bind("<<TreeviewSelect>>", self.on_chat_tab_select)

        # Add a scrollbar to the tab_frame
        scrollbar = ttk.Scrollbar(self.tab_frame, orient="vertical", command=self.tab_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tab_tree.configure(yscrollcommand=scrollbar.set)

        # Create buttons frame
        btn_frame = ttk.Frame(self.sidebar)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.add_tab_btn = ttk.Button(btn_frame, text="+ Tab", command=self.add_new_tab)
        self.add_tab_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.add_subtab_btn = ttk.Button(btn_frame, text="+ Sub", command=self.add_new_subtab, state=tk.DISABLED)
        self.add_subtab_btn.pack(side="left", fill="x", expand=True, padx=2)
        
        self.delete_chat_btn = ttk.Button(self.sidebar, text="🗑 Delete Chat", command=self.delete_chat)
        self.delete_chat_btn.pack(side="left", padx=4)

        self.rename_chat_btn = ttk.Button(self.sidebar, text="✏️ Rename Chat", command=self.rename_chat)
        self.rename_chat_btn.pack(side="left", padx=4)


        # Create main content frame (existing UI)
        self.main_frame = ttk.Frame(self.paned)
        self.paned.add(self.main_frame, weight=1)

        # Move existing UI to main_frame
        self.status = ttk.Label(self.main_frame, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=5, anchor="w", padx=10)

        text_frame = ttk.Frame(self.main_frame)
        text_frame.pack(fill="both", expand=True, padx=10)

        self.response_box = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
                                    bg='#343541', fg='white', insertbackground='white', selectbackground='#4E4E4E',
                                    highlightthickness=0)
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.insert(tk.END, "🤖 Start a new conversation or ask your first question...")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.tag_configure('code', foreground='#4EC9B0')

        scrollbar = ttk.Scrollbar(text_frame, command=self.response_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.response_box.config(yscrollcommand=scrollbar.set)

        # Button bar above chat entry
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.record_btn = ttk.Button(control_frame, text="🎤 Listen", command=self.toggle_recording)
        self.record_btn.pack(side="left", padx=4)
        
        self.toggle_input_btn = ttk.Button(control_frame, text="🔈 Internal Audio (BlackHole)", command=self.toggle_input_mode)
        self.toggle_input_btn.pack(side="left", padx=4)


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
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 14), width=80)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(5, 10))

        self.input_entry.bind("<Return>", lambda event: self.submit_text_question())

        self.submit_btn = ttk.Button(input_frame, text="➡️", width=4, command=self.submit_text_question)
        self.submit_btn.pack(side="right")

    def load_chat_tabs(self):
        print("Chat Tabs:", self.chat_tabs)  # Debugging line
        self.chat_tabs.delete(*self.chat_tabs.get_children())
        for i, title in enumerate(self.chat_manager.get_titles()):
            self.chat_tabs.insert("", "end", iid=f"chat_{i}", text=title)
            
    def delete_chat(self):
        selected = self.chat_tabs.selection()
        if not selected:
            messagebox.showwarning("No Chat Selected", "Please select a chat first")
            return

        # Get the chat index from the selected tab
        tab_id = selected[0]
        if tab_id.startswith("chat_"):
            index = int(tab_id.split("_")[1])
            title = self.chat_manager.get_titles()[index]
            
            # Ask for confirmation before deletion
            confirm = messagebox.askyesno("Delete Chat", f"Are you sure you want to delete the chat '{title}'?")
            if confirm:
                # Remove chat from chat history manager
                self.chat_manager.sessions.pop(index)
                self.chat_manager.save()

                # Remove the chat from the sidebar UI
                self.chat_tabs.delete(tab_id)

                self.status.config(text=f"❌ Deleted chat: {title}")
                print(f"Deleted chat: {title}")

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

    def on_tab_select(self, event):
        selected = self.tab_tree.selection()
        if not selected:
            self.current_tab = -1
            self.current_subtab = -1
            return

        item_id = selected[0]
        if item_id.startswith("tab_"):
            self.current_tab = int(item_id.split("_")[1])
            self.current_subtab = -1
            self.add_subtab_btn.config(state=tk.NORMAL)
        elif item_id.startswith("sub_"):
            parts = item_id.split("_")
            self.current_tab = int(parts[1])
            self.current_subtab = int(parts[2])
            self.add_subtab_btn.config(state=tk.NORMAL)

            prompt = self.prompt_manager.get_subtab_prompt(self.current_tab, self.current_subtab)
            text_input = self.prompt_manager.get_subtab_text_input(self.current_tab, self.current_subtab)

            if prompt:
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, prompt)

            if text_input and not self.assistant.streaming:
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, text_input)
                self.submit_text_question()


        
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

        if any(c["type"] == "image_url" for c in content):
            self.assistant.messages.append({
                "role": "user",
                "content": content  # send as structured list when image is present
            })
        else:
            self.assistant.messages.append({
                "role": "user",
                "content": flat_text  # send as plain text when no image
            })


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
        with self.toggle_lock:  # Ensure only one action is triggered at a time
            if self.is_processing_audio:
                print("⏳ Already processing. Please wait.")
                return

            if not self.assistant.recorder.is_recording:
                self.assistant.streaming = False
                self.response_box.config(state=tk.NORMAL)
                self.response_box.insert(tk.END, "\n\n🎙 Listening to your question...\n")
                self.response_box.config(state=tk.DISABLED)
                self.response_box.see(tk.END)

                self.assistant.recorder.start_recording()
                self.status.config(text="🎙 Listening to interviewer...")
                self.record_btn.config(text="🛑 Stop & Process")
                self.stop_btn.config(state=tk.DISABLED)
            else:
                self.is_processing_audio = True  # Set flag to True when processing audio
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
            # Show updated history before streaming
            self.display_chat_history()

            self.status.config(text="💡 Generating answer...")
            self.assistant.cancel_streaming()
            self.assistant.stream_gpt_response(self.response_box, self.status, self.record_btn)

        finally:
            self.is_processing_audio = False  # Reset the flag after processing is complete






    def start_new_chat(self):
    # Save current session if not empty
        if len(self.assistant.messages) > 1:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.chat_manager.add_session(timestamp, self.assistant.messages.copy())
            self.chat_manager.save()  # ✅ Ensure the file is written
            self.load_chat_tabs()

        # Start fresh session
        self.assistant.messages = [{
            "role": "system",
            "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."
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

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))

    # Define this AFTER app is created
    def setup_hotkey_listener():
        from pynput import keyboard
        combo_upload_resume = {keyboard.KeyCode(char='2'), keyboard.KeyCode(char='3')}
        combo_focus_chatbox = {keyboard.KeyCode(char='1'), keyboard.KeyCode(char='2')}
        combo_toggle_input_mode = {keyboard.KeyCode(char='3'), keyboard.KeyCode(char='4')}
        combo_listen_external = {keyboard.KeyCode(char='5'), keyboard.KeyCode(char='6')}
        combo_increase_font = {keyboard.Key.cmd, keyboard.KeyCode(char='=')}   # Cmd + +
        combo_decrease_font = {keyboard.Key.cmd, keyboard.KeyCode(char='-')}   # Cmd + -
        combo_pin_window     = {keyboard.Key.cmd, keyboard.KeyCode(char='p')}  # Cmd + P




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

            # Track combo key state
            
            if key in combo_focus_chatbox or key in combo_upload_resume or key in combo_toggle_input_mode or key in combo_listen_external or key in combo_increase_font or key in combo_decrease_font or key in combo_pin_window:
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
                    print("🔍 Global hotkey Cmd + -: Decrease font")
                    app.decrease_font()
                elif combo_pin_window.issubset(current_keys):
                    print("📌 Global hotkey Cmd + P: Toggle pin")
                    app.toggle_always_on_top()

                        

            
                    
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
            print("🧠 Global hotkey ~: Stop generating answer")
            app.stop_output()

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

                app.status.config(text="📎 Full screen screenshot attached. Press Enter to send.")
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

