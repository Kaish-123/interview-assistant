
import ssl
import urllib.request
import tkinter as tk
from tkinter import ttk, font, filedialog
import threading
import wave
import pyaudio
import whisper
from datetime import datetime
import requests
from openai import OpenAI
import sqlite3
import os
from pdfminer.high_level import extract_text
from docx import Document
import pytesseract
from PIL import Image

# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context

# CONFIG
API_KEY = "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"

client = OpenAI(api_key=API_KEY)
model = whisper.load_model("base")

from PIL import ImageTk  # Ensure this import is present at the top

def handle_paste(self, event=None):
    from PIL import ImageGrab
    import pyperclip

    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            # Save temporarily
            tmp_path = os.path.join(os.path.expanduser("~"), f"pasted_img_{datetime.now().timestamp()}.png")
            image.save(tmp_path)

            # Show thumbnail in chat
            thumb = image.copy()
            thumb.thumbnail((100, 100))
            image_tk = ImageTk.PhotoImage(thumb)

            chat_box = self.chat_widgets[self.current_conversation]
            chat_box.config(state=tk.NORMAL)
            chat_box.image_create(tk.END, image=image_tk)
            chat_box.insert(tk.END, "\n📎 Image ready to send. Click 'Send'.\n\n")
            chat_box.config(state=tk.DISABLED)

            self.image_refs.append(image_tk)
            self.pending_attachments.append(tmp_path)
        else:
            pasted_text = pyperclip.paste()
            if pasted_text.strip():
                self.db.save_message(self.current_conversation, "user", pasted_text.strip())
                box = self.chat_widgets[self.current_conversation]
                box.config(state=tk.NORMAL)
                box.insert(tk.END, f"👤 You: {pasted_text.strip()}\n\n")
                box.config(state=tk.DISABLED)

    except Exception as e:
        self.status.config(text=f"❌ Paste failed: {e}")
        
def send_pending_attachments(self):
    if not self.pending_attachments:
        self.status.config(text="⚠️ No attachments to send.")
        return

    # Construct vision-supported message format
    vision_message = [
        {"type": "text", "text": "Please analyze the following image(s)."}
    ]

    for img_path in self.pending_attachments:
        with open(img_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
            vision_message.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_img}"}
            })

    # Save message log
    box = self.chat_widgets[self.current_conversation]
    box.config(state=tk.NORMAL)
    box.insert(tk.END, f"👤 You: [Attached {len(self.pending_attachments)} Image(s)]\n\n")
    box.config(state=tk.DISABLED)

    # Construct structured vision message
    vision_message = [{"type": "text", "text": "Please analyze the following image(s)."}]
    for img_path in self.pending_attachments:
        with open(img_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")
            vision_message.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_img}"}
            })

    self.pending_attachments.clear()

    self.status.config(text="💡 Analyzing image with GPT-4 Vision...")
    threading.Thread(
        target=self.ask_and_display_response,
        args=(vision_message,),
        daemon=True
    ).start()




def ask_and_display_response(self, content):
    answer = self.ask_gpt(content)
    self.db.save_message(self.current_conversation, "assistant", answer)

    box = self.chat_widgets[self.current_conversation]
    box.config(state=tk.NORMAL)
    box.insert(tk.END, f"🤖 Assistant: {answer}\n\n")
    box.config(state=tk.DISABLED)
    self.status.config(text="✅ Done")






class ChatDatabase:
    def __init__(self):
        self.db_path = os.path.expanduser("~/interview_chats.db")
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            conversation_id INTEGER,
            content TEXT,
            role TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            conversation_id INTEGER,
            file_name TEXT,
            file_content BLOB,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        )""")
        self.conn.commit()

    def create_conversation(self, title):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO conversations (title) VALUES (?)", (title,))
        self.conn.commit()
        return cursor.lastrowid

    def save_message(self, conversation_id, role, content):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?)""", (conversation_id, role, content))
        self.conn.commit()

    def save_document(self, conversation_id, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO documents (conversation_id, file_name, file_content)
        VALUES (?, ?, ?)""", (conversation_id, os.path.basename(file_path), content))
        self.conn.commit()
        
    def get_conversations(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title FROM conversations ORDER BY created_at DESC")
        return cursor.fetchall()

    def get_messages(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT role, content FROM messages 
        WHERE conversation_id = ? ORDER BY created_at""", (conversation_id,))
        return cursor.fetchall()

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path):
        try:
            if file_path.lower().endswith('.pdf'):
                return extract_text(file_path)
            elif file_path.lower().endswith('.docx'):
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                return pytesseract.image_to_string(Image.open(file_path))
            else:
                with open(file_path, 'r') as f:
                    return f.read()
        except Exception as e:
            return f"❌ Document error: {str(e)}"

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatGPT Voice Assistant")
        self.geometry("900x600")
        self.minsize(700, 500)
        self.bind_all("<Command-v>", self.handle_paste)  # macOS
        self.bind_all("<Control-v>", self.handle_paste)  # Windows/Linux fallback
        self.pending_attachments = []   # Holds file paths
        self.image_refs = []            # Prevents garbage collection of images



        self.db = ChatDatabase()
        self.current_conversation = None
        self.chat_widgets = {}

        self.default_font_size = 12
        self.current_font = font.Font(family="Arial", size=self.default_font_size)
        self.is_listening = False

        self.setup_sidebar()
        self.setup_main_content()
        self.new_conversation()

    def setup_sidebar(self):
        self.sidebar = ttk.Frame(self, width=200)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        self.new_chat_btn = ttk.Button(self.sidebar, text="➕ New Chat", command=self.new_conversation)
        self.new_chat_btn.pack(fill="x", pady=5)

        self.upload_btn = ttk.Button(self.sidebar, text="📁 Upload Document", command=self.upload_document)
        self.upload_btn.pack(fill="x", pady=5)

        self.conversation_list = tk.Listbox(self.sidebar)
        self.conversation_list.pack(fill="both", expand=True)
        self.conversation_list.bind('<<ListboxSelect>>', self.load_selected_conversation)

    def setup_main_content(self):
        self.main_content = ttk.Frame(self)
        self.main_content.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.status = tk.Label(self.main_content, text="🔊 Waiting for input...", font=self.current_font)
        self.status.pack(pady=5)

        self.tabs = ttk.Notebook(self.main_content)
        self.tabs.pack(expand=True, fill="both")

        self.billing_label = tk.Label(self.main_content, text="💳 Checking usage...", font=("Arial", 10))
        self.billing_label.pack(pady=5)

        self.btn_frame = tk.Frame(self.main_content)
        self.btn_frame.pack(fill="x")

        tk.Button(self.btn_frame, text="A+", command=self.increase_font).pack(side="left")
        tk.Button(self.btn_frame, text="A-", command=self.decrease_font).pack(side="left")

        self.record_btn = tk.Button(
            self.btn_frame,
            text="🎙 Ask ChatGPT",
            font=self.current_font,
            bg="#28a745",
            fg="white",
            command=self.toggle_recording
        )
        self.record_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.send_btn = tk.Button(
            self.btn_frame,
            text="📤 Send",
            font=self.current_font,
            bg="#007bff",
            fg="white",
            command=self.send_pending_attachments
        )
        self.send_btn.pack(side="left", padx=5)


        threading.Thread(target=self.check_billing).start()

    def new_conversation(self):
        conv_id = self.db.create_conversation(f"Interview {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.current_conversation = conv_id
        self._add_chat_tab(conv_id)
        self.refresh_conversations()

    def _add_chat_tab(self, conversation_id):
        frame = ttk.Frame(self.tabs)
        text_box = tk.Text(frame, wrap=tk.WORD, font=self.current_font)
        text_box.pack(expand=True, fill="both")
        text_box.insert(tk.END, "🤖 New conversation started...\n")
        text_box.config(state=tk.DISABLED)

        self.chat_widgets[conversation_id] = text_box
        title = self.db.get_conversations()[0][1]
        self.tabs.add(frame, text=title)
        self.tabs.select(len(self.tabs.tabs()) - 1)

    def refresh_conversations(self):
        self.conversation_list.delete(0, tk.END)
        for conv_id, title in self.db.get_conversations():
            self.conversation_list.insert(tk.END, title)

    def load_selected_conversation(self, event):
        idx = self.conversation_list.curselection()
        if not idx:
            return
        conv_id = self.db.get_conversations()[idx[0]][0]
        self.current_conversation = conv_id

        if conv_id not in self.chat_widgets:
            self._add_chat_tab(conv_id)

        self.tabs.select(self.chat_widgets[conv_id].master)
        self.load_messages(conv_id)

    def load_messages(self, conversation_id):
        widget = self.chat_widgets[conversation_id]
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        for role, content in self.db.get_messages(conversation_id):
            prefix = "👤 You: " if role == "user" else "🤖 Assistant: "
            widget.insert(tk.END, prefix + content + "\n\n")
        widget.config(state=tk.DISABLED)

    def upload_document(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Documents", "*.pdf *.docx *.txt"), ("Images", "*.png *.jpg *.jpeg")
        ])
        if file_path and self.current_conversation:
            self.db.save_document(self.current_conversation, file_path)
            content = DocumentProcessor.extract_text(file_path)
            widget = self.chat_widgets[self.current_conversation]
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, "[Document Upload]\n" + content[:1000] + "\n")
            widget.config(state=tk.DISABLED)

    def record_until_stop(self, file="input.wav"):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        frames = []
        self.status.config(text="🎙 Listening...")

        self.is_listening = True
        while self.is_listening:
            frames.append(stream.read(1024))

        stream.stop_stream()
        stream.close()
        p.terminate()
        with wave.open(file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))
        return file

    def transcribe_audio(self, file):
        return model.transcribe(file)["text"]

    def ask_gpt(self, prompt):
        try:
            messages = self.db.get_messages(self.current_conversation)
            history = [{"role": r, "content": c} for r, c in messages]

            if isinstance(prompt, list):  # structured for image + text
                history.append({"role": "user", "content": prompt})  # ✅ correct format
                model_to_use = "gpt-4-vision-preview"
            else:
                history.append({"role": "user", "content": prompt})
                model_to_use = "gpt-3.5-turbo"

            # 👇 FIX: if any message has content as list, ensure it's passed as-is
            response = client.chat.completions.create(
                model=model_to_use,
                messages=history,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ GPT Error: {e}"



    def full_process(self):
        file = self.record_until_stop()
        question = self.transcribe_audio(file)
        self.status.config(text=f"❓ {question}")
        self.db.save_message(self.current_conversation, "user", question)

        answer = self.ask_gpt(question)
        self.db.save_message(self.current_conversation, "assistant", answer)

        box = self.chat_widgets[self.current_conversation]
        box.config(state=tk.NORMAL)
        box.insert(tk.END, f"👤 You: {question}\n\n🤖 Assistant: {answer}\n\n")
        box.config(state=tk.DISABLED)
        self.status.config(text="✅ Done")

    def toggle_recording(self):
        if not self.is_listening:
            self.is_listening = True
            self.record_btn.config(text="🛑 Listening...")
            threading.Thread(target=self.full_process).start()
        else:
            self.is_listening = False
            self.record_btn.config(text="🎙 Ask ChatGPT")

    def check_billing(self):
        try:
            headers = {"Authorization": f"Bearer {API_KEY}"}
            usage = requests.get("https://api.openai.com/v1/dashboard/billing/usage?start_date=2024-01-01&end_date=2025-12-31", headers=headers).json()
            limit = requests.get("https://api.openai.com/v1/dashboard/billing/subscription", headers=headers).json()
            used = usage.get("total_usage", 0) / 100.0
            cap = limit.get("hard_limit_usd", 0)
            self.billing_label.config(text=f"💰 Used: ${used:.2f} / ${cap:.2f}")
        except:
            self.billing_label.config(text="⚠️ Billing info not available")

    def increase_font(self):
        self.default_font_size += 1
        self.current_font.config(size=self.default_font_size)
        for widget in self.chat_widgets.values():
            widget.config(font=self.current_font)

    def decrease_font(self):
        if self.default_font_size > 8:
            self.default_font_size -= 1
            self.current_font.config(size=self.default_font_size)
            for widget in self.chat_widgets.values():
                widget.config(font=self.current_font)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
