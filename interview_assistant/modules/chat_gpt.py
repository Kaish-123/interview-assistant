from modules.audio_recorder import AudioRecorder  # Add this line
from openai import OpenAI
from config.settings import Settings
import threading
import time
import re
import tkinter as tk

class ChatGPTAssistant:
    def __init__(self):
        self.settings = Settings()
        self.client = OpenAI(api_key=self.settings.API_KEY)
        self.recorder = AudioRecorder()
        self.streaming = False
        self.current_response = ""
        self.current_question = ""
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12
        
    def transcribe_audio(self, filename):
        try:
            with open(filename, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model=self.settings.WHISPER_MODEL,
                    file=audio_file
                )
            return transcription.text
        except Exception as e:
            if "Connection" in str(e):
                return "❌ Transcription: Check internet connection"
            return f"❌ Transcription error: {str(e)}"

    def stream_gpt_response(self, prompt, text_widget, status_label, button):
        with self.lock:
            self.current_question = prompt
            self.current_response = ""
            self.streaming = True
            
            try:
                stream = self.client.chat.completions.create(
                    model=self.settings.GPT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    timeout=10  # Add timeout
                )
                # ... rest of the original code ...
            except Exception as e:
                error_msg = "Connection error" if "Connection" in str(e) else str(e)
                self.current_response = f"❌ GPT Error: {error_msg}"
                self.update_text_widget(text_widget)
    
    def update_text_widget(self, text_widget):
        self.last_scroll_position = text_widget.yview()[0]
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, f"Question: {self.current_question}\n\nAnswer: {self.current_response}")
        self.highlight_code(text_widget)
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