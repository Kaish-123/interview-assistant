import sounddevice as sd
import numpy as np
import wave
import threading
from openai import OpenAI
import tkinter as tk
from tkinter import ttk, font
import re
import time
import queue

# Configuration
API_KEY = API_KEY = "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"
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
        self.current_question = ""
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12
        
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
    
    def stream_gpt_response(self, prompt, text_widget, status_label, button):
        with self.lock:
            self.current_question = prompt
            self.current_response = ""
            self.streaming = True
            
            try:
                stream = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                
                # Batch updates to reduce flickering
                buffer = ""
                last_update = time.time()
                
                for chunk in stream:
                    if not self.streaming:
                        break
                        
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        buffer += content
                        
                        # Update every 100ms or when buffer gets large
                        if time.time() - last_update > 0.1 or len(buffer) > 30:
                            self.current_response += buffer
                            self.update_text_widget(text_widget)
                            buffer = ""
                            last_update = time.time()
                
                # Flush remaining buffer
                if buffer:
                    self.current_response += buffer
                    self.update_text_widget(text_widget)
                
            except Exception as e:
                self.current_response = f"❌ GPT Error: {str(e)}"
                self.update_text_widget(text_widget)
            
            finally:
                self.streaming = False
                button.config(state=tk.NORMAL)
                status_label.config(text="✅ Ready")
    
    def update_text_widget(self, text_widget):
        # Save current scroll position
        self.last_scroll_position = text_widget.yview()[0]
        
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        
        # Display question and answer
        text_widget.insert(tk.END, f"Question: {self.current_question}\n\n")
        text_widget.insert(tk.END, "Answer: ")
        text_widget.insert(tk.END, self.current_response)
        
        self.highlight_code(text_widget)
        
        # Restore scroll position if not at bottom
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
        self.geometry("800x600")
        self.configure(bg='#343541')
        self.always_on_top = False
        
        self.assistant = ChatGPTAssistant()
        self.setup_ui()
        
    def setup_ui(self):
        # Status Label
        self.status = ttk.Label(self, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=10)
        
        # Response Box with Frame
        text_frame = ttk.Frame(self)
        text_frame.pack(pady=5, fill="both", expand=True, padx=10)
        
        self.response_box = tk.Text(
            text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
            bg='#343541', fg='white', insertbackground='white',
            selectbackground='#4E4E4E', highlightthickness=0
        )
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.insert(tk.END, "🤖 Response will appear here...")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.tag_configure('code', foreground='#4EC9B0')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=self.response_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.response_box.config(yscrollcommand=scrollbar.set)
        
        # Button Frame
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        # Control Buttons
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
        
        # Font Controls
        font_frame = ttk.Frame(button_frame)
        font_frame.pack(side="left", padx=10)
        
        ttk.Button(font_frame, text="A+", command=self.increase_font).pack(side="left", padx=2)
        ttk.Button(font_frame, text="A-", command=self.decrease_font).pack(side="left", padx=2)
        
        # Always on Top Toggle
        self.topmost_btn = ttk.Button(
            button_frame, text="📌 Pin Window", 
            command=self.toggle_always_on_top
        )
        self.topmost_btn.pack(side="right", padx=5)
        
    def toggle_recording(self):
        if not self.assistant.recorder.is_recording:
            # Start fresh recording
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
            # Stop recording and process
            self.record_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status.config(text="💭 Processing question...")
            
            threading.Thread(
                target=self.process_recording,
                daemon=True
            ).start()
    
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
        
        # Start streaming response
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

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    
    app.mainloop()
