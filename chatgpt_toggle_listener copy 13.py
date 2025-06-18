import ssl
import urllib.request
import tkinter as tk
from tkinter import font
import threading
import wave
import pyaudio
import whisper
from datetime import datetime
import requests
from openai import OpenAI

# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context

# CONFIG
API_KEY = "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"

client = OpenAI(api_key=API_KEY)
model = whisper.load_model("base")

# GUI Setup
root = tk.Tk()
root.title("ChatGPT Voice Assistant")
root.geometry("400x300")
root.minsize(300, 200)
root.resizable(True, True)
root.attributes("-topmost", True)

# Font controls
default_font_size = 12
current_font = font.Font(family="Arial", size=default_font_size)

# State
is_listening = False
recording_thread = None

# Widgets
status = tk.Label(root, text="🔊 Waiting for input...", font=current_font)
status.pack(pady=10)

response_box = tk.Text(root, height=5, wrap=tk.WORD, font=current_font)
response_box.pack(pady=5, fill="both", expand=True)
response_box.insert(tk.END, "🤖 Response will appear here...")
response_box.config(state=tk.DISABLED)

billing_label = tk.Label(root, text="💳 Checking usage...", font=("Arial", 10))
billing_label.pack(pady=5)

# Audio Functions
def record_until_stop(file="input.wav"):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
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

def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

def full_process():
    file = record_until_stop()
    question = transcribe_audio(file)
    status.config(text=f"❓ {question}")
    response = ask_gpt(question)
    response_box.config(state=tk.NORMAL)
    response_box.delete(1.0, tk.END)
    response_box.insert(tk.END, response)
    response_box.config(state=tk.DISABLED)
    status.config(text="✅ Ready for next...")

def toggle_recording():
    global is_listening, recording_thread
    if not is_listening:
        is_listening = True
        record_btn.config(text="🛑 Listening... Click to stop")
        recording_thread = threading.Thread(target=full_process)
        recording_thread.start()
    else:
        is_listening = False
        record_btn.config(text="🎙 Ask ChatGPT")

def check_billing():
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        usage = requests.get("https://api.openai.com/v1/dashboard/billing/usage?start_date=2024-01-01&end_date=2025-12-31", headers=headers).json()
        limit = requests.get("https://api.openai.com/v1/dashboard/billing/subscription", headers=headers).json()
        used = usage.get("total_usage", 0) / 100.0
        hard_limit = limit.get("hard_limit_usd", 0)
        billing_label.config(text=f"💰 Used: ${used:.2f} / ${hard_limit:.2f}")
    except:
        billing_label.config(text="⚠️ Billing info not available")

threading.Thread(target=check_billing).start()

# Font Controls
def increase_font():
    global default_font_size
    default_font_size += 1
    current_font.config(size=default_font_size)

def decrease_font():
    global default_font_size
    if default_font_size > 8:
        default_font_size -= 1
        current_font.config(size=default_font_size)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

increase_btn = tk.Button(btn_frame, text="A+", command=increase_font)
increase_btn.pack(side="left", padx=5)

decrease_btn = tk.Button(btn_frame, text="A-", command=decrease_font)
decrease_btn.pack(side="left", padx=5)

record_btn = tk.Button(btn_frame, text="🎙 Ask ChatGPT", font=current_font, bg="#28a745", fg="white", command=toggle_recording)
record_btn.pack(side="left", padx=5, fill="both", expand=True)

def minimize(): root.iconify()
root.after(1000, minimize)

root.mainloop()
