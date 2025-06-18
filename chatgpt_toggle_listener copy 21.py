import sounddevice as sd
import numpy as np
import wave
import threading
from openai import OpenAI
import tkinter as tk
from tkinter import ttk, font, messagebox
import re
import time
import queue
import uuid
from datetime import datetime

# Configuration
API_KEY = "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"
client = OpenAI(api_key=API_KEY)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
CHUNK = 1024
BLACKHOLE_DEVICE = "BlackHole"

class ChatSession:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.messages = [{"role": "system", "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."}]
        self.title = "New Chat"
        self.active = True

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
        self.chat_sessions = []
        self.current_chat = None
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12
        
        # Start with initial chat
        self.create_new_chat()
        
    def create_new_chat(self):
        if self.current_chat:
            self.current_chat.active = False
        new_chat = ChatSession()
        self.chat_sessions.append(new_chat)
        self.current_chat = new_chat
        return new_chat
    
    def switch_chat(self, chat_id):
        for chat in self.chat_sessions:
            if chat.id == chat_id:
                self.current_chat = chat
                return True
        return False
    
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
    
    def generate_chat_title(self, first_question):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"Generate a short 3-5 word title for this question: {first_question}"
                }]
            )
            return response.choices[0].message.content.strip('"')
        except:
            return first_question[:20] + "..." if len(first_question) > 20 else first_question
    
    def stream_gpt_response(self, text_widget, status_label, button):
        with self.lock:
            self.current_response = ""
            self.streaming = True
            
            try:
                stream = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=self.current_chat.messages,
                    stream=True
                )
                
                buffer = ""
                last_update = time.time()
                
                for chunk in stream:
                    if not self.streaming:
                        break
                        
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        buffer += content
                        
                        if time.time() - last_update > 0.1 or len(buffer) > 30:
                            self.current_response += buffer
                            self.update_text_widget(text_widget)
                            buffer = ""
                            last_update = time.time()
                
                if buffer:
                    self.current_response += buffer
                    self.update_text_widget(text_widget)
                
                # Add completed response to history
                self.current_chat.messages.append({"role": "assistant", "content": self.current_response})
                
                # Update chat title if it's the first interaction
                if len(self.current_chat.messages) == 2:  # system + first response
                    first_question = self.current_chat.messages[1]['content']
                    self.current_chat.title = self.generate_chat_title(first_question)
            
            except Exception as e:
                self.current_response = f"❌ GPT Error: {str(e)}"
                self.update_text_widget(text_widget)
            
            finally:
                self.streaming = False
                button.config(state=tk.NORMAL)
                status_label.config(text="✅ Ready")
    
    def update_text_widget(self, text_widget):
        self.last_scroll_position = text_widget.yview()[0]
        
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        
        # Display conversation history
        for msg in self.current_chat.messages:
            if msg['role'] == 'system':
                continue
            prefix = "Question: " if msg['role'] == 'user' else "Answer: "
            text_widget.insert(tk.END, f"{prefix}{msg['content']}\n\n")
        
        # Add current streaming response
        if self.streaming:
            text_widget.insert(tk.END, f"Answer: {self.current_response}")
        
        self.highlight_code(text_widget)
        
        if self.last_scroll_position != 1.0:
            text_widget.yview_moveto(self.last_scroll_position)
        else:
            text_widget.see(tk.END)
            
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
        self.title("Interview Assistant")
        self.geometry("1000x600")
        self.configure(bg='#343541')
        self.always_on_top = False
        
        self.assistant = ChatGPTAssistant()
        self.setup_ui()
        self.update_chat_list()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Chat list panel
        self.chat_list_frame = ttk.Frame(main_frame, width=200)
        self.chat_list_frame.pack(side="left", fill="y", padx=5)
        
        self.chat_listbox = tk.Listbox(
            self.chat_list_frame,
            bg='#2d2d2d',
            fg='white',
            selectbackground='#404040',
            font=('Arial', 10),
            relief="flat"
        )
        self.chat_listbox.pack(fill="both", expand=True, pady=5)
        self.chat_listbox.bind('<<ListboxSelect>>', self.on_chat_select)
        
        # Main content panel
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side="right", fill="both", expand=True)
        
        self.status = ttk.Label(content_frame, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=10)

        input_frame = ttk.Frame(content_frame)
        input_frame.pack(pady=5, fill="x", padx=10)

        self.input_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)

        self.submit_btn = ttk.Button(
            input_frame, text="✍️ Submit Question",
            command=self.submit_text_question
        )
        self.submit_btn.pack(side="right")

        text_frame = ttk.Frame(content_frame)
        text_frame.pack(pady=5, fill="both", expand=True, padx=10)

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

        button_frame = ttk.Frame(content_frame)
        button_frame.pack(pady=10)

        self.record_btn = ttk.Button(
            button_frame, text="🎤 Start Listening",
            command=self.toggle_recording
        )
        self.record_btn.pack(side="left", padx=5)

        self.new_chat_btn = ttk.Button(
            button_frame, text="🆕 New Chat",
            command=self.start_new_chat
        )
        self.new_chat_btn.pack(side="left", padx=5)

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

    def update_chat_list(self):
        self.chat_listbox.delete(0, tk.END)
        for chat in self.assistant.chat_sessions:
            timestamp = chat.created_at.strftime("%H:%M")
            self.chat_listbox.insert(tk.END, f"{timestamp} - {chat.title}")
            if chat.id == self.assistant.current_chat.id:
                self.chat_listbox.selection_set(tk.END)

    def on_chat_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            selected_chat = self.assistant.chat_sessions[index]
            if selected_chat.id != self.assistant.current_chat.id:
                self.assistant.switch_chat(selected_chat.id)
                self.response_box.config(state=tk.NORMAL)
                self.response_box.delete(1.0, tk.END)
                for msg in selected_chat.messages:
                    if msg['role'] == 'system':
                        continue
                    prefix = "Question: " if msg['role'] == 'user' else "Answer: "
                    self.response_box.insert(tk.END, f"{prefix}{msg['content']}\n\n")
                self.response_box.config(state=tk.DISABLED)
                self.status.config(text=f"↩️ Switched to chat: {selected_chat.title}")

    def toggle_recording(self):
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
            self.record_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status.config(text="💭 Processing question...")
            threading.Thread(target=self.process_recording, daemon=True).start()

    def process_recording(self):
        filename = self.assistant.recorder.stop_recording()
        question = self.assistant.transcribe_audio(filename)
        if question.startswith("❌"):
            self.status.config(text=question)
            return
        self.assistant.current_chat.messages.append({"role": "user", "content": question})
        self.status.config(text="💡 Generating answer...")
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(self.response_box, self.status, self.record_btn),
            daemon=True
        ).start()

    def submit_text_question(self):
        question = self.input_entry.get().strip()
        if not question:
            return
        self.input_entry.delete(0, tk.END)
        self.assistant.current_chat.messages.append({"role": "user", "content": question})
        self.status.config(text="💡 Generating answer...")
        threading.Thread(
            target=self.assistant.stream_gpt_response,
            args=(self.response_box, self.status, self.record_btn),
            daemon=True
        ).start()

    def start_new_chat(self):
        self.assistant.create_new_chat()
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, "🤖 New conversation started...")
        self.response_box.config(state=tk.DISABLED)
        self.status.config(text="🆕 New chat started")
        self.update_chat_list()

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
    app.mainloop()