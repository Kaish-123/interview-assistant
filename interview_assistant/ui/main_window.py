import threading
import queue
import time
import tkinter as tk
from tkinter import ttk
from modules.chat_gpt import ChatGPTAssistant
from config import styles

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interview Assistant")
        self.geometry("800x600")
        self.configure(bg=styles.BG_COLOR)
        self.always_on_top = False
        self.assistant = ChatGPTAssistant()
        self._setup_ui()
        self._setup_styles()
        
    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure('TLabel', background=styles.BG_COLOR, foreground=styles.TEXT_COLOR)
        self.style.configure('TButton', **styles.BUTTON_STYLE)
        
    def _setup_ui(self):
        self.status = ttk.Label(self, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=10)

        input_frame = ttk.Frame(self)
        input_frame.pack(pady=5, fill="x", padx=10)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)

        self.submit_btn = ttk.Button(
            input_frame, text="✍️ Submit Question",
            command=self.submit_text_question
        )
        self.submit_btn.pack(side="right")

        text_frame = ttk.Frame(self)
        text_frame.pack(pady=5, fill="both", expand=True, padx=10)

        self.response_box = tk.Text(
            text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
            bg=styles.BG_COLOR, fg=styles.TEXT_COLOR, insertbackground='white',
            selectbackground='#4E4E4E', highlightthickness=0
        )
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.insert(tk.END, "🤖 Response will appear here...")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.tag_configure('code', foreground=styles.CODE_COLOR)

        scrollbar = ttk.Scrollbar(text_frame, command=self.response_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.response_box.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        self.record_btn = ttk.Button(
            button_frame, text="🎤 Start Listening",
            command=self.toggle_recording
        )
        self.record_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(
            button_frame, text="⏹ Stop Output",
            command=self.stop_output,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side="left", padx=5)

        font_frame = ttk.Frame(button_frame)
        font_frame.pack(side="left", padx=10)

        ttk.Button(font_frame, text="A+", command=self.increase_font).pack(side="left", padx=2)
        ttk.Button(font_frame, text="A-", command=self.decrease_font).pack(side="left", padx=2)

        self.topmost_btn = ttk.Button(
            button_frame, text="📌 Pin Window",
            command=self.toggle_always_on_top
        )
        self.topmost_btn.pack(side="right", padx=5)
        
    # Add these methods INSIDE the Application class in ui/main_window.py

from modules.utils import check_internet_connection  # Add this import

def toggle_recording(self):
    if not check_internet_connection():
        self.status.config(text="❌ No internet connection")
        return
    
    # Rest of the original toggle_recording code...

def submit_text_question(self):
    if not check_internet_connection():
        self.status.config(text="❌ No internet connection")
        return
    
    # Rest of the original submit_text_question code...
    def stop_output(self):
        self.assistant.streaming = False
        self.stop_btn.config(state=tk.DISABLED)
        self.status.config(text="⏹ Output stopped")

    def process_recording(self):
        filename = self.assistant.recorder.stop_recording()
        question = self.assistant.transcribe_audio(filename)
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, f"Question: {question}\n\nAnswer: ")
        self.response_box.config(state=tk.DISABLED)
        self.status.config(text="💡 Generating answer...")
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(question, self.response_box, self.status, self.record_btn),
            daemon=True
        ).start()

    def submit_text_question(self):  # THIS WAS MISSING
        question = self.input_entry.get().strip()
        if not question:
            return
        self.input_entry.delete(0, tk.END)
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, f"Question: {question}\n\nAnswer: ")
        self.response_box.config(state=tk.DISABLED)
        self.status.config(text="💡 Generating answer...")
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(question, self.response_box, self.status, self.record_btn),
            daemon=True
        ).start()

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

    # Add all remaining application methods here (toggle_recording, stop_output, etc.)
    # ... [Keep all the original Application class methods from your code]