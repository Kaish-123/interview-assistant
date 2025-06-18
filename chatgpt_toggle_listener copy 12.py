# Updated full code for Interview Assistant with persistent chat history and document upload support

import os
import json
import sounddevice as sd
import numpy as np
import wave
import threading
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from openai import OpenAI
import re
import time
import queue
import ctypes
import PyPDF2

# CONFIGURATION
API_KEY = "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"
client = OpenAI(api_key=API_KEY)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
CHUNK = 1024
BLACKHOLE_DEVICE = "BlackHole"

# Ensure session folder exists
os.makedirs("sessions", exist_ok=True)
session_name = simpledialog.askstring("Session", "Enter session name:")
session_file = f"sessions/{session_name}.json"
if os.path.exists(session_file):
    with open(session_file, "r") as f:
        session_data = json.load(f)
else:
    session_data = {"resume": "", "jd": "", "messages": []}


def terminate_thread(thread):
    if not thread.is_alive():
        return
    tid = ctypes.c_long(thread.ident)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(SystemExit))
    if res == 0:
        raise ValueError("Invalid thread ID")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("Thread termination failed")


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
        self.stream_thread = None

    def transcribe_audio(self, filename):
        try:
            with open(filename, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcription.text
        except Exception as e:
            return f"\u274c Transcription error: {str(e)}"

    def stream_gpt_response(self, prompt, text_widget, status_label, button):
        def stream_task():
            with self.lock:
                self.current_question = prompt
                self.current_response = ""
                self.streaming = True
                try:
                    messages = []
                    if session_data.get("resume"):
                        messages.append({"role": "system", "content": f"Resume:\n{session_data['resume']}"})
                    if session_data.get("jd"):
                        messages.append({"role": "system", "content": f"Job Description:\n{session_data['jd']}"})
                    messages += session_data["messages"][-6:]
                    messages.append({"role": "user", "content": prompt})

                    stream = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=messages,
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

                    session_data["messages"].append({"role": "user", "content": prompt})
                    session_data["messages"].append({"role": "assistant", "content": self.current_response})
                    with open(session_file, "w") as f:
                        json.dump(session_data, f, indent=2)

                except Exception as e:
                    self.current_response = f"\u274c GPT Error: {str(e)}"
                    self.update_text_widget(text_widget)
                finally:
                    self.streaming = False
                    button.config(state=tk.NORMAL)
                    status_label.config(text="\u2705 Ready")

        self.stream_thread = threading.Thread(target=stream_task, daemon=True)
        self.stream_thread.start()

    def stop_all(self):
        self.streaming = False
        if self.stream_thread and self.stream_thread.is_alive():
            try:
                terminate_thread(self.stream_thread)
            except Exception as e:
                print(f"Thread termination error: {e}")

    def update_text_widget(self, text_widget):
        self.last_scroll_position = text_widget.yview()[0]
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, f"Question: {self.current_question}\n\nAnswer: ")
        text_widget.insert(tk.END, self.current_response)
        text_widget.config(state=tk.DISABLED)
        text_widget.update_idletasks()


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interview Assistant")
        self.geometry("800x600")
        self.configure(bg='#343541')
        self.assistant = ChatGPTAssistant()
        self.setup_ui()

    def setup_ui(self):
        self.status = ttk.Label(self, text="\U0001F50A Ready")
        self.status.pack(pady=10)

        self.upload_frame = ttk.Frame(self)
        self.upload_frame.pack(pady=5)
        ttk.Button(self.upload_frame, text="\U0001F4CE Upload Resume", command=self.upload_resume).pack(side="left", padx=5)
        ttk.Button(self.upload_frame, text="\U0001F4C4 Upload JD", command=self.upload_jd).pack(side="left", padx=5)

        self.response_box = tk.Text(self, wrap=tk.WORD, font=('Consolas', 12), bg='#343541', fg='white')
        self.response_box.pack(expand=True, fill='both', padx=10, pady=10)
        self.response_box.insert(tk.END, "\U0001F916 Response will appear here...")
        self.response_box.config(state=tk.DISABLED)

        self.input_entry = ttk.Entry(self, font=('Arial', 12))
        self.input_entry.pack(fill="x", padx=10)
        ttk.Button(self, text="\u270D Submit", command=self.submit_question).pack(pady=5)

    def upload_resume(self):
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'rb') as f:
                if path.endswith('.pdf'):
                    reader = PyPDF2.PdfReader(f)
                    session_data["resume"] = "\n".join([p.extract_text() for p in reader.pages])
                else:
                    session_data["resume"] = f.read().decode("utf-8")
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)

    def upload_jd(self):
        path = filedialog.askopenfilename()
        if path:
            with open(path, 'rb') as f:
                if path.endswith('.pdf'):
                    reader = PyPDF2.PdfReader(f)
                    session_data["jd"] = "\n".join([p.extract_text() for p in reader.pages])
                else:
                    session_data["jd"] = f.read().decode("utf-8")
            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)

    def submit_question(self):
        question = self.input_entry.get().strip()
        if question:
            self.input_entry.delete(0, tk.END)
            self.response_box.config(state=tk.NORMAL)
            self.response_box.delete(1.0, tk.END)
            self.response_box.insert(tk.END, f"Question: {question}\n\nAnswer: ")
            self.response_box.config(state=tk.DISABLED)
            self.status.config(text="\U0001F4A1 Thinking...")
            threading.Thread(target=self.assistant.stream_gpt_response, args=(question, self.response_box, self.status, self), daemon=True).start()

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    app.mainloop()