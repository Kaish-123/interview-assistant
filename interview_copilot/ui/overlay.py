"""Live floating overlay — listen, auto-answer, screen analyze, notes."""

from __future__ import annotations

import os
import tempfile
import threading
import time
import queue
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

import numpy as np
import sounddevice as sd
from PIL import ImageGrab

from interview_copilot.core.audio import AudioRecorder
from interview_copilot.core.config import (
    MIN_RECORD_SECS,
    ONSET_CHUNKS,
    SILENCE_SECS,
    SPEECH_RMS,
)
from interview_copilot.core.llm import AssistantEngine
from interview_copilot.core.session import new_session_id, save_notes, save_session


class OverlayWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, session_cfg: dict):
        super().__init__(master)
        self.session_cfg = session_cfg
        self.session_id = new_session_id()
        self.title("Interview Copilot — Live")
        self.geometry("520x680+40+40")
        self.minsize(420, 480)
        self.configure(bg="#0b1016")
        self.attributes("-topmost", True)

        self.engine = AssistantEngine(
            model=session_cfg["model"],
            language=session_cfg["language"],
        )
        self.engine.set_context(
            resume=session_cfg.get("resume", ""),
            job_description=session_cfg.get("job_description", ""),
            extra=session_cfg.get("extra", ""),
        )

        self.recorder = AudioRecorder()
        self.recorder.input_mode = session_cfg.get("audio_mode", "internal")

        self.listening = False
        self._vad_running = False
        self._busy = False
        self.transcript_log: list[dict] = []
        self.status_var = tk.StringVar(value="Ready — press Start Listening")
        self.auto_answer = bool(session_cfg.get("auto_answer", True))

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Command-Return>", lambda e: self._manual_ask())
        self.bind("<Control-Return>", lambda e: self._manual_ask())
        self.bind("<Command-Shift-a>", lambda e: self._analyze_screen())
        self.bind("<Control-Shift-a>", lambda e: self._analyze_screen())
        self.bind("<Command-l>", lambda e: self._toggle_listen())
        self.bind("<Control-l>", lambda e: self._toggle_listen())

    def _build(self):
        top = tk.Frame(self, bg="#0b1016")
        top.pack(fill="x", padx=12, pady=(12, 6))

        self.listen_btn = ttk.Button(top, text="▶ Start Listening", command=self._toggle_listen)
        self.listen_btn.pack(side="left", padx=(0, 6))
        ttk.Button(top, text="🖥 Analyze Screen", command=self._analyze_screen).pack(side="left", padx=3)
        ttk.Button(top, text="📝 End + Notes", command=self._end_with_notes).pack(side="left", padx=3)

        tk.Label(
            self,
            textvariable=self.status_var,
            fg="#8aa0b5",
            bg="#0b1016",
            anchor="w",
            font=("Helvetica Neue", 10),
        ).pack(fill="x", padx=12)

        # Live transcript / question
        tk.Label(self, text="Heard / Question", fg="#c5d4e3", bg="#0b1016").pack(anchor="w", padx=12)
        self.question_box = tk.Text(
            self, height=4, wrap="word", bg="#151d28", fg="#e8eef5",
            insertbackground="#e8eef5", relief="flat", font=("Menlo", 11),
        )
        self.question_box.pack(fill="x", padx=12, pady=(2, 8))

        # Answer
        tk.Label(self, text="Suggested answer", fg="#c5d4e3", bg="#0b1016").pack(anchor="w", padx=12)
        self.answer_box = tk.Text(
            self, wrap="word", bg="#151d28", fg="#e8eef5",
            insertbackground="#e8eef5", relief="flat", font=("Helvetica Neue", 12),
        )
        self.answer_box.pack(fill="both", expand=True, padx=12, pady=(2, 8))

        # Manual message
        bottom = tk.Frame(self, bg="#0b1016")
        bottom.pack(fill="x", padx=12, pady=(0, 12))
        self.manual_entry = tk.Entry(
            bottom, bg="#1a2330", fg="#e8eef5", insertbackground="#e8eef5",
            relief="flat", font=("Helvetica Neue", 12),
        )
        self.manual_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.manual_entry.bind("<Return>", lambda e: self._manual_ask())
        ttk.Button(bottom, text="Ask", command=self._manual_ask).pack(side="left", padx=(8, 0))

        hint = tk.Label(
            self,
            text="Shortcuts: ⌘L listen · ⌘⇧A analyze screen · ⌘⏎ ask",
            fg="#5f7388",
            bg="#0b1016",
            font=("Helvetica Neue", 9),
        )
        hint.pack(anchor="w", padx=12, pady=(0, 10))

    # ── Listening / VAD ──────────────────────────────────────────────────
    def _toggle_listen(self):
        if self.listening:
            self.listening = False
            self._vad_running = False
            self.listen_btn.config(text="▶ Start Listening")
            self.status_var.set("Listening stopped")
            return

        self.listening = True
        self._vad_running = True
        self.listen_btn.config(text="■ Stop Listening")
        self.status_var.set("Listening for questions…")
        threading.Thread(target=self._vad_loop, daemon=True, name="copilot-vad").start()

    def _vad_loop(self):
        device_id = self.recorder.find_device()
        try:
            info = sd.query_devices(device_id) if device_id is not None else sd.query_devices(sd.default.device[0])
            n_channels = max(1, min(int(info.get("max_input_channels", 1)), 8))
            native_sr = int(info.get("default_samplerate", 48000))
        except Exception:
            n_channels, native_sr = 1, 48000

        rms_q: queue.Queue = queue.Queue(maxsize=200)
        block = max(native_sr // 10, 512)

        def cb(indata, frames, t, status):
            mono = indata.mean(axis=1) if indata.ndim > 1 else indata[:, 0]
            rms = float(np.sqrt(np.mean(mono.astype(np.float32) ** 2)))
            try:
                rms_q.put_nowait(rms)
            except queue.Full:
                pass

        stream = None
        onset = 0
        speaking = False
        silence_start = None
        rec_start = None

        try:
            stream = sd.InputStream(
                device=device_id,
                samplerate=native_sr,
                channels=n_channels,
                dtype="float32",
                blocksize=block,
                callback=cb,
            )
            stream.start()

            while self._vad_running and self.listening:
                try:
                    rms = rms_q.get(timeout=0.4)
                except queue.Empty:
                    continue

                if self._busy:
                    continue

                if not speaking:
                    if rms > SPEECH_RMS:
                        onset += 1
                        if onset >= ONSET_CHUNKS and not self.recorder.is_recording:
                            speaking = True
                            silence_start = None
                            rec_start = time.time()
                            self.recorder.start_recording()
                            self.after(0, lambda: self.status_var.set("Recording question…"))
                    else:
                        onset = max(0, onset - 1)
                else:
                    if not self.recorder.is_recording:
                        speaking = False
                        onset = 0
                        continue
                    elapsed = time.time() - (rec_start or time.time())
                    if rms > SPEECH_RMS:
                        silence_start = None
                    elif elapsed >= MIN_RECORD_SECS:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= SILENCE_SECS:
                            speaking = False
                            silence_start = None
                            onset = 0
                            self.after(0, self._finish_utterance)
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Audio error: {e}"))
        finally:
            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass
            self._vad_running = False

    def _finish_utterance(self):
        if self._busy:
            return
        self._busy = True
        self.status_var.set("Transcribing…")

        def work():
            path = None
            start_answer = None
            try:
                fd, path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                saved = self.recorder.stop_recording(path)
                if not saved:
                    self.after(0, lambda: self._done_idle("Too short — still listening"))
                    return
                text = self.engine.transcribe(saved)
                if not text:
                    self.after(0, lambda: self._done_idle("No speech detected — listening"))
                    return
                self.after(0, lambda: self._set_question(text))
                if self.auto_answer and self.engine.looks_like_question(text):
                    start_answer = text
                else:
                    self.after(0, lambda: self._done_idle(
                        "Heard — press Ask or wait for a clear question"
                    ))
                    return
            except Exception as e:
                self.after(0, lambda: self._done_idle(f"Error: {e}"))
                return
            finally:
                if path:
                    try:
                        os.remove(path)
                    except Exception:
                        pass

            if start_answer:
                self.after(0, lambda t=start_answer: self._stream_answer_async(t))

        threading.Thread(target=work, daemon=True).start()

    def _done_idle(self, status: str):
        self._busy = False
        self.status_var.set(status)
        if self.listening:
            self.after(
                1200,
                lambda: self.status_var.set("Listening for questions…")
                if self.listening and not self._busy
                else None,
            )

    # ── Answers ──────────────────────────────────────────────────────────
    def _set_question(self, text: str):
        self.question_box.delete("1.0", "end")
        self.question_box.insert("1.0", text)
        self.transcript_log.append({"role": "heard", "text": text, "ts": time.time()})

    def _clear_answer(self):
        self.answer_box.delete("1.0", "end")

    def _append_answer(self, chunk: str):
        self.answer_box.insert("end", chunk)
        self.answer_box.see("end")

    def _stream_answer_async(self, question: str):
        self._busy = True
        self.status_var.set("Generating answer…")
        self._clear_answer()

        def work():
            try:
                for chunk in self.engine.stream_answer(question):
                    self.after(0, lambda c=chunk: self._append_answer(c))
                self.after(0, lambda: self._done_idle("Answer ready"))
            except Exception as e:
                self.after(0, lambda: self._done_idle(f"LLM error: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def _manual_ask(self):
        if self._busy:
            return
        q = self.manual_entry.get().strip()
        if not q:
            q = self.question_box.get("1.0", "end").strip()
        if not q:
            return
        self.manual_entry.delete(0, "end")
        self._set_question(q)
        self._stream_answer_async(q)

    def _analyze_screen(self):
        if self._busy:
            return
        self._busy = True
        self.status_var.set("Capturing screen…")
        self._clear_answer()
        self._set_question("[Screen analysis]")

        def work():
            try:
                shot = ImageGrab.grab()
                self.after(0, lambda: self.status_var.set("Analyzing coding problem…"))
                for chunk in self.engine.analyze_screenshot(shot):
                    self.after(0, lambda c=chunk: self._append_answer(c))
                self.after(0, lambda: self._done_idle("Screen analysis ready"))
            except Exception as e:
                self.after(0, lambda: self._done_idle(f"Screen error: {e}"))

        threading.Thread(target=work, daemon=True).start()

    # ── End session ──────────────────────────────────────────────────────
    def _end_with_notes(self):
        if self._busy:
            messagebox.showinfo("Busy", "Wait for the current answer to finish.")
            return
        self.listening = False
        self._vad_running = False
        self.status_var.set("Generating post-call notes…")

        def work():
            try:
                notes = self.engine.generate_notes()
                npath = save_notes(self.session_id, notes)
                spath = save_session(
                    self.session_id,
                    {
                        "config": {
                            k: v for k, v in self.session_cfg.items() if k != "resume"
                        },
                        "resume_attached": bool(self.session_cfg.get("resume")),
                        "messages": self.engine.messages,
                        "heard": self.transcript_log,
                        "notes_path": str(npath),
                    },
                )
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Session saved",
                        f"Notes:\n{npath}\n\nSession:\n{spath}",
                    ),
                )
                self.after(0, self._on_close)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Notes failed", str(e)))
                self.after(0, lambda: self.status_var.set(f"Notes error: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def _on_close(self):
        self.listening = False
        self._vad_running = False
        try:
            self.master.destroy()
        except Exception:
            self.destroy()
