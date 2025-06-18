import ssl
import urllib.request
import tkinter as tk
from tkinter import font, scrolledtext
import threading
import wave
import pyaudio
import whisper
from datetime import datetime
import requests
from openai import OpenAI
import re
from tkinter import ttk
import time

# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context

# CONFIG
API_KEY = "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" # Replace with your actual API key

client = OpenAI(api_key=API_KEY)
model = whisper.load_model("base")

class CodeText(tk.Text):
    """Custom text widget for syntax highlighting"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_configure('python', foreground='#3572A5')
        self.tag_configure('bash', foreground='#89E051')
        self.tag_configure('javascript', foreground='#F1E05A')
        self.tag_configure('html', foreground='#E34C26')
        self.tag_configure('css', foreground='#563D7C')
        self.tag_configure('json', foreground='#2596BE')
        self.tag_configure('markdown', foreground='#083FA1')
        self.tag_configure('comment', foreground='#6A9955')
        self.tag_configure('string', foreground='#CE9178')
        self.tag_configure('keyword', foreground='#C586C0')
        self.tag_configure('function', foreground='#DCDCAA')
        self.tag_configure('background', background='#1E1E1E')

def highlight_code(text_widget):
    """Apply syntax highlighting to code blocks"""
    content = text_widget.get("1.0", tk.END)
    text_widget.config(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)
    
    # Clear all tags first
    for tag in text_widget.tag_names():
        text_widget.tag_remove(tag, "1.0", tk.END)
    
    # Find all code blocks
    code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
    
    if not code_blocks:
        text_widget.insert(tk.END, content)
        return
    
    last_pos = 0
    for lang, code in code_blocks:
        # Insert text before code block
        pre_text = content[last_pos:content.find(f'```{lang}\n{code}```', last_pos)]
        text_widget.insert(tk.END, pre_text)
        
        # Insert and highlight code
        start = text_widget.index(tk.INSERT)
        text_widget.insert(tk.END, code, (lang if lang else 'python'))
        end = text_widget.index(tk.INSERT)
        
        # Apply language-specific highlighting
        if lang:
            text_widget.tag_add(lang, start, end)
        
        last_pos = content.find(f'```{lang}\n{code}```', last_pos) + len(f'```{lang}\n{code}```')
    
    # Insert remaining text after last code block
    text_widget.insert(tk.END, content[last_pos:])
    text_widget.config(state=tk.DISABLED)

# GUI Setup
root = tk.Tk()
root.title("ChatGPT Voice Assistant")
root.geometry("800x600")
root.minsize(600, 400)
root.configure(bg='#343541')

# Custom style
style = ttk.Style()
style.configure('TButton', font=('Arial', 12))
style.configure('TLabel', background='#343541', foreground='white')

# Font controls
default_font = font.Font(family="Consolas", size=12)
text_font = font.Font(family="Consolas", size=12)

# State
is_listening = False
recording_thread = None
streaming = False
current_response = ""

# Widgets
status = ttk.Label(root, text="🔊 Waiting for input...", style='TLabel')
status.pack(pady=10)

response_box = CodeText(root, wrap=tk.WORD, font=text_font, bg='#343541', fg='white',
                      insertbackground='white', selectbackground='#4E4E4E')
response_box.pack(pady=5, fill="both", expand=True, padx=10)
response_box.insert(tk.END, "🤖 Response will appear here...")
response_box.config(state=tk.DISABLED)

scrollbar = ttk.Scrollbar(response_box)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
response_box.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=response_box.yview)

billing_label = ttk.Label(root, text="💳 Checking usage...", style='TLabel')
billing_label.pack(pady=5)

# Audio Functions
def record_until_stop(file="input.wav"):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, 
                   input=True, frames_per_buffer=1024)
    frames = []
    status.config(text="🎙 Listening... Click to stop")

    while is_listening:
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()
    
    with wave.open(file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    return file

def transcribe_audio(file):
    return model.transcribe(file)["text"]

def stream_gpt_response(prompt):
    global streaming, current_response
    
    response_box.config(state=tk.NORMAL)
    response_box.delete(1.0, tk.END)
    current_response = ""
    streaming = True
    
    try:
        stream = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Format code responses with Markdown code blocks."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        for chunk in stream:
            if not streaming:  # Stop if user interrupted
                break
                
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                current_response += content
                
                # Update the GUI in real-time
                response_box.delete(1.0, tk.END)
                response_box.insert(tk.END, current_response)
                highlight_code(response_box)
                
                # Auto-scroll to bottom
                response_box.see(tk.END)
                root.update()
                
                # Small delay for natural typing effect
                time.sleep(0.02)
                
    except Exception as e:
        current_response = f"❌ GPT Error: {str(e)}"
        response_box.delete(1.0, tk.END)
        response_box.insert(tk.END, current_response)
    
    streaming = False
    response_box.config(state=tk.DISABLED)
    status.config(text="✅ Ready for next...")

def full_process():
    file = record_until_stop()
    question = transcribe_audio(file)
    status.config(text=f"❓ {question}")
    
    # Start streaming response in a separate thread
    threading.Thread(target=stream_gpt_response, args=(question,), daemon=True).start()

def toggle_recording():
    global is_listening, streaming
    
    if not is_listening:
        # Start listening
        is_listening = True
        streaming = False
        record_btn.config(text="🛑 Stop Listening")
        threading.Thread(target=full_process, daemon=True).start()
    else:
        # Stop listening/streaming
        is_listening = False
        streaming = False
        record_btn.config(text="🎙 Start Listening")

def check_billing():
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        usage = requests.get("https://api.openai.com/v1/dashboard/billing/usage", 
                          headers=headers).json()
        limit = requests.get("https://api.openai.com/v1/dashboard/billing/subscription", 
                          headers=headers).json()
        used = usage.get("total_usage", 0) / 100.0
        hard_limit = limit.get("hard_limit_usd", 0)
        billing_label.config(text=f"💰 Used: ${used:.2f} / ${hard_limit:.2f}")
    except:
        billing_label.config(text="⚠️ Billing info not available")

# Control Panel
control_frame = ttk.Frame(root)
control_frame.pack(pady=10)

record_btn = ttk.Button(control_frame, text="🎙 Start Listening", 
                       command=toggle_recording, style='TButton')
record_btn.pack(side=tk.LEFT, padx=5)

font_frame = ttk.Frame(control_frame)
font_frame.pack(side=tk.LEFT, padx=10)

def increase_font():
    current_size = text_font.cget("size")
    text_font.config(size=current_size + 1)
    response_box.config(font=text_font)

def decrease_font():
    current_size = text_font.cget("size")
    if current_size > 8:
        text_font.config(size=current_size - 1)
        response_box.config(font=text_font)

ttk.Button(font_frame, text="A+", command=increase_font).pack(side=tk.LEFT)
ttk.Button(font_frame, text="A-", command=decrease_font).pack(side=tk.LEFT)

# Start background threads
threading.Thread(target=check_billing, daemon=True).start()

root.mainloop()
