import sounddevice as sd
import numpy as np
import wave
import threading
from openai import OpenAI
import tkinter as tk
from tkinter import ttk, font
import re
import time

# Configuration
API_KEY = "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"
client = OpenAI(api_key=API_KEY)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
CHUNK = 1024
BLACKHOLE_DEVICE = "BlackHole"  # Virtual audio device name

# Audio Capture Setup
class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.stream = None
        
    def find_blackhole_device(self):
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if BLACKHOLE_DEVICE in device['name']:
                return i
        raise ValueError("BlackHole device not found. Install it from https://existential.audio/blackhole/")

    def start_recording(self):
        device_id = self.find_blackhole_device()
        self.frames = []
        self.is_recording = True
        
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.frames.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=callback,
            device=device_id
        )
        self.stream.start()

    def stop_recording(self, filename="interviewer.wav"):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if self.frames:
            audio_data = np.concatenate(self.frames)
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())
        return filename

# GPT Interface
class ChatGPTAssistant:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.streaming = False
        self.current_response = ""
        
    def transcribe_audio(self, filename):
        audio_file = open(filename, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcription.text
    
    def stream_gpt_response(self, prompt, text_widget):
        self.current_response = ""
        self.streaming = True
        
        stream = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        
        for chunk in stream:
            if not self.streaming:
                break
                
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                self.current_response += content
                
                text_widget.config(state=tk.NORMAL)
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, self.current_response)
                self.highlight_code(text_widget)
                text_widget.see(tk.END)
                text_widget.config(state=tk.DISABLED)
                text_widget.update()
                time.sleep(0.02)
        
        self.streaming = False
    
    def highlight_code(self, text_widget):
        content = text_widget.get("1.0", tk.END)
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        
        # Simple code block highlighting
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
        last_pos = 0
        
        for lang, code in code_blocks:
            pre_text = content[last_pos:content.find(f'```{lang}\n{code}```', last_pos)]
            text_widget.insert(tk.END, pre_text)
            
            start = text_widget.index(tk.INSERT)
            text_widget.insert(tk.END, code, ('code'))
            end = text_widget.index(tk.INSERT)
            text_widget.tag_add('code', start, end)
            
            last_pos = content.find(f'```{lang}\n{code}```', last_pos) + len(f'```{lang}\n{code}```')
        
        text_widget.insert(tk.END, content[last_pos:])
        text_widget.config(state=tk.DISABLED)

# GUI Setup
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interview Assistant")
        self.geometry("800x600")
        self.configure(bg='#343541')
        
        self.assistant = ChatGPTAssistant()
        self.setup_ui()
        
    def setup_ui(self):
        # Status Label
        self.status = ttk.Label(self, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=10)
        
        # Response Box
        self.response_box = tk.Text(
            self, wrap=tk.WORD, font=('Consolas', 12),
            bg='#343541', fg='white', insertbackground='white',
            selectbackground='#4E4E4E'
        )
        self.response_box.pack(pady=5, fill="both", expand=True, padx=10)
        self.response_box.insert(tk.END, "🤖 Response will appear here...")
        self.response_box.config(state=tk.DISABLED)
        self.response_box.tag_configure('code', foreground='#4EC9B0')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.response_box)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_box.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.response_box.yview)
        
        # Control Button
        self.record_btn = ttk.Button(
            self, text="🎤 Start Listening", 
            command=self.toggle_recording
        )
        self.record_btn.pack(pady=10)
        
    def toggle_recording(self):
        if not self.assistant.recorder.is_recording:
            # Start recording
            self.assistant.recorder.start_recording()
            self.status.config(text="🎙 Listening to interviewer...")
            self.record_btn.config(text="🛑 Stop & Process")
        else:
            # Stop recording and process
            filename = self.assistant.recorder.stop_recording()
            self.status.config(text="💭 Processing question...")
            self.record_btn.config(state=tk.DISABLED)
            
            # Transcribe and get response in background
            threading.Thread(target=self.process_question, args=(filename,), daemon=True).start()
    
    def process_question(self, filename):
        question = self.assistant.transcribe_audio(filename)
        self.status.config(text=f"❓ Question: {question}")
        
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, f"Question: {question}\n\nAnswer: ")
        self.response_box.config(state=tk.DISABLED)
        
        self.assistant.stream_gpt_response(question, self.response_box)
        
        self.status.config(text="✅ Ready")
        self.record_btn.config(text="🎤 Start Listening", state=tk.NORMAL)

# Run the application
if __name__ == "__main__":
    # Setup BlackHole first (one-time setup)
    print("""
    Before running:
    1. Install BlackHole: https://existential.audio/blackhole/
    2. Set BlackHole as input in Audio MIDI Setup
    3. Configure Zoom to output to BlackHole
    """)
    
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    
    app.mainloop()
