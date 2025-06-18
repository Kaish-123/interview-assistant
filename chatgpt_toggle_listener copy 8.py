
# Configuration

# >>> Copy from here
import sounddevice as sd
import numpy as np
import wave
import threading
import tkinter as tk
from tkinter import ttk
import re
import time
import queue
import base64
import io
from PIL import ImageGrab
from openai import OpenAI

# Configuration
API_KEY = "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"

client = OpenAI(api_key=API_KEY)
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
CHUNK = 1024

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.audio_queue = queue.Queue()
        self.device_name = "BlackHole"

    def set_device(self, name):
        self.device_name = name

    def find_device(self):
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if self.device_name in device['name']:
                return i
        raise ValueError(f"Device '{self.device_name}' not found")

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

            except Exception as e:
                self.current_response = f"❌ GPT Error: {str(e)}"
                self.update_text_widget(text_widget)
            finally:
                self.streaming = False
                button.config(state=tk.NORMAL)
                status_label.config(text="✅ Ready")

    def ask_about_image(self, image, text_widget, status_label, button):
        self.streaming = True
        self.current_response = ""
        self.current_question = "[Image Input]"

        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_base64 = base64.b64encode(image_bytes.getvalue()).decode("utf-8")

        try:
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": "What does this image say or show?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]}
                ],
                max_tokens=1000
            )
            self.current_response = response.choices[0].message.content
        except Exception as e:
            self.current_response = f"❌ GPT Vision Error: {str(e)}"

        self.update_text_widget(text_widget)
        self.streaming = False
        button.config(state=tk.NORMAL)
        status_label.config(text="✅ Ready")

    def update_text_widget(self, text_widget):
        self.last_scroll_position = text_widget.yview()[0]
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, f"Question: {self.current_question}\n\nAnswer: ")
        text_widget.insert(tk.END, self.current_response)
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
        self.geometry("800x600")
        self.configure(bg='#343541')
        self.always_on_top = False
        self.assistant = ChatGPTAssistant()
        self.setup_ui()

    def setup_ui(self):
        self.status = ttk.Label(self, text="🔊 Ready", style='TLabel')
        self.status.pack(pady=10)

        device_frame = ttk.Frame(self)
        device_frame.pack(pady=5)
        ttk.Label(device_frame, text="🎧 Input Device:", background='#343541', foreground='white').pack(side="left", padx=5)
        self.device_selector = ttk.Combobox(device_frame, values=self.get_audio_devices(), state='readonly', width=40)
        self.device_selector.pack(side="left", padx=5)
        self.device_selector.set("BlackHole")
        self.device_selector.bind("<<ComboboxSelected>>", self.change_input_device)

        input_frame = ttk.Frame(self)
        input_frame.pack(pady=5, fill="x", padx=10)
        self.input_entry = ttk.Entry(input_frame, font=('Arial', 12))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(input_frame, text="✍️ Submit Question", command=self.submit_text_question).pack(side="right")

        text_frame = ttk.Frame(self)
        text_frame.pack(pady=5, fill="both", expand=True, padx=10)
        self.response_box = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 12), bg='#343541', fg='white', insertbackground='white')
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.config(state=tk.DISABLED)
        self.response_box.tag_configure('code', foreground='#4EC9B0')
        scrollbar = ttk.Scrollbar(text_frame, command=self.response_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.response_box.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="🎤 Start Listening", command=self.toggle_recording).pack(side="left", padx=5)
        ttk.Button(button_frame, text="⏹ Stop Output", command=self.stop_output).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🖼️ Ask from Screenshot", command=self.capture_screenshot_and_ask).pack(side="left", padx=5)
        ttk.Button(button_frame, text="A+", command=self.increase_font).pack(side="left", padx=2)
        ttk.Button(button_frame, text="A-", command=self.decrease_font).pack(side="left", padx=2)
        ttk.Button(button_frame, text="📌 Pin Window", command=self.toggle_always_on_top).pack(side="right", padx=5)

    def get_audio_devices(self):
        return [d['name'] for d in sd.query_devices() if d['max_input_channels'] > 0]

    def change_input_device(self, event=None):
        self.assistant.recorder.set_device(self.device_selector.get())

    def toggle_recording(self):
        if not self.assistant.recorder.is_recording:
            self.assistant.streaming = False
            self.response_box.config(state=tk.NORMAL)
            self.response_box.delete(1.0, tk.END)
            self.response_box.insert(tk.END, "Listening...")
            self.response_box.config(state=tk.DISABLED)
            self.assistant.recorder.set_device(self.device_selector.get())
            self.assistant.recorder.start_recording()
            self.status.config(text="🎙 Listening to interviewer...")
        else:
            threading.Thread(target=self.process_recording, daemon=True).start()

    def stop_output(self):
        self.assistant.streaming = False
        self.status.config(text="⏹ Output stopped")

    def process_recording(self):
        filename = self.assistant.recorder.stop_recording()
        question = self.assistant.transcribe_audio(filename)
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, f"Question: {question}\n\nAnswer: ")
        self.response_box.config(state=tk.DISABLED)
        self.status.config(text="💡 Generating answer...")
        threading.Thread(target=self.assistant.stream_gpt_response,
                         args=(question, self.response_box, self.status, None),
                         daemon=True).start()

    def submit_text_question(self):
        question = self.input_entry.get().strip()
        if not question:
            return
        self.input_entry.delete(0, tk.END)
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, f"Question: {question}\n\nAnswer: ")
        self.response_box.config(state=tk.DISABLED)
        self.status.config(text="💡 Generating answer...")
        threading.Thread(target=self.assistant.stream_gpt_response,
                         args=(question, self.response_box, self.status, None),
                         daemon=True).start()

    def capture_screenshot_and_ask(self):
        self.withdraw()
        time.sleep(0.5)
        bbox = self.select_screen_area()
        if bbox:
            screenshot = ImageGrab.grab(bbox)
            self.deiconify()
            self.response_box.config(state=tk.NORMAL)
            self.response_box.delete(1.0, tk.END)
            self.response_box.insert(tk.END, "Processing screenshot...")
            self.response_box.config(state=tk.DISABLED)
            threading.Thread(target=self.assistant.ask_about_image,
                             args=(screenshot, self.response_box, self.status, None),
                             daemon=True).start()
        else:
            self.deiconify()

    def select_screen_area(self):
        root = tk.Toplevel()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.configure(bg='gray')
        canvas = tk.Canvas(root, cursor="cross", bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)
        coords = {}
        def on_mouse_down(e): coords.update(x1=e.x, y1=e.y)
        def on_mouse_up(e):
            coords.update(x2=e.x, y2=e.y)
            root.destroy()
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        root.mainloop()
        if 'x1' in coords and 'x2' in coords:
            return (min(coords['x1'], coords['x2']), min(coords['y1'], coords['y2']),
                    max(coords['x1'], coords['x2']), max(coords['y1'], coords['y2']))
        return None

    def increase_font(self):
        self.assistant.font_size += 1
        self.response_box.config(font=('Consolas', self.assistant.font_size))

    def decrease_font(self):
        self.assistant.font_size -= 1
        self.response_box.config(font=('Consolas', self.assistant.font_size))

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.attributes("-topmost", self.always_on_top)

if __name__ == "__main__":
    app = Application()
    style = ttk.Style()
    style.configure('TLabel', background='#343541', foreground='white')
    style.configure('TButton', font=('Arial', 12))
    app.mainloop()
# <<< Copy till here