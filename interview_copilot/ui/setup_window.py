"""Session setup — resume, JD, model, language (Parakeet-style start flow)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from interview_copilot.core.config import DEFAULT_MODEL, LANGUAGES, MODELS, OPENAI_API_KEY


def _read_text_file(path: str) -> str:
    p = Path(path)
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        # Fallback for odd encodings / binary-ish docs
        return p.read_bytes().decode("utf-8", errors="ignore")


class SetupWindow(tk.Tk):
    def __init__(self, on_start: Callable[[dict], None]):
        super().__init__()
        self.on_start = on_start
        self.title("Interview Copilot — New Session")
        self.geometry("720x640")
        self.minsize(640, 560)
        self.configure(bg="#0f1419")

        self.resume_text = ""
        self.resume_name = tk.StringVar(value="No resume attached")
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.lang_var = tk.StringVar(value="en")
        self.audio_var = tk.StringVar(value="internal")
        self.auto_answer_var = tk.BooleanVar(value=True)

        self._build()

        if not OPENAI_API_KEY:
            messagebox.showwarning(
                "API key missing",
                "OPENAI_API_KEY not found in .env.\nAdd it before starting a session.",
            )

    def _build(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        pad = {"padx": 16, "pady": 6}
        header = tk.Label(
            self,
            text="Interview Copilot",
            font=("Helvetica Neue", 22, "bold"),
            fg="#e8eef5",
            bg="#0f1419",
        )
        header.pack(anchor="w", padx=16, pady=(18, 2))
        sub = tk.Label(
            self,
            text="Real-time transcription → suggested answers → coding screen analysis → post-call notes",
            font=("Helvetica Neue", 11),
            fg="#8aa0b5",
            bg="#0f1419",
            wraplength=680,
            justify="left",
        )
        sub.pack(anchor="w", padx=16, pady=(0, 10))

        form = tk.Frame(self, bg="#0f1419")
        form.pack(fill="both", expand=True, **pad)

        # Resume
        row = tk.Frame(form, bg="#0f1419")
        row.pack(fill="x", pady=4)
        ttk.Button(row, text="Upload Resume", command=self._pick_resume).pack(side="left")
        tk.Label(row, textvariable=self.resume_name, fg="#c5d4e3", bg="#0f1419").pack(
            side="left", padx=10
        )

        # Job description
        tk.Label(form, text="Job description", fg="#c5d4e3", bg="#0f1419").pack(anchor="w")
        self.jd_box = tk.Text(form, height=6, wrap="word", bg="#1a2330", fg="#e8eef5",
                              insertbackground="#e8eef5", relief="flat", font=("Menlo", 11))
        self.jd_box.pack(fill="x", pady=(2, 8))

        # Extra context
        tk.Label(form, text="Extra context / instructions", fg="#c5d4e3", bg="#0f1419").pack(anchor="w")
        self.extra_box = tk.Text(form, height=4, wrap="word", bg="#1a2330", fg="#e8eef5",
                                 insertbackground="#e8eef5", relief="flat", font=("Menlo", 11))
        self.extra_box.pack(fill="x", pady=(2, 8))

        opts = tk.Frame(form, bg="#0f1419")
        opts.pack(fill="x", pady=6)

        tk.Label(opts, text="Model", fg="#c5d4e3", bg="#0f1419").grid(row=0, column=0, sticky="w")
        model_cb = ttk.Combobox(
            opts,
            textvariable=self.model_var,
            values=list(MODELS.keys()),
            state="readonly",
            width=18,
        )
        model_cb.grid(row=0, column=1, padx=(8, 20), sticky="w")

        tk.Label(opts, text="Language", fg="#c5d4e3", bg="#0f1419").grid(row=0, column=2, sticky="w")
        lang_cb = ttk.Combobox(
            opts, textvariable=self.lang_var, values=LANGUAGES, state="readonly", width=8
        )
        lang_cb.grid(row=0, column=3, padx=8, sticky="w")

        tk.Label(opts, text="Audio source", fg="#c5d4e3", bg="#0f1419").grid(row=1, column=0, sticky="w", pady=(10, 0))
        audio_cb = ttk.Combobox(
            opts,
            textvariable=self.audio_var,
            values=["internal", "external"],
            state="readonly",
            width=18,
        )
        audio_cb.grid(row=1, column=1, padx=(8, 20), sticky="w", pady=(10, 0))
        hint = tk.Label(
            opts,
            text="internal = BlackHole system audio (Zoom/Meet via headphones)\nexternal = microphone",
            fg="#6f8499",
            bg="#0f1419",
            justify="left",
        )
        hint.grid(row=1, column=2, columnspan=2, sticky="w", pady=(10, 0))

        ttk.Checkbutton(
            form,
            text="Auto-answer when a question is detected (Parakeet-style)",
            variable=self.auto_answer_var,
        ).pack(anchor="w", pady=10)

        foot = tk.Frame(self, bg="#0f1419")
        foot.pack(fill="x", padx=16, pady=16)
        ttk.Button(foot, text="Start Session", command=self._start).pack(side="right")

    def _pick_resume(self):
        path = filedialog.askopenfilename(
            title="Select resume",
            filetypes=[
                ("Text / Markdown / PDF text", "*.txt *.md *.markdown *.pdf *.rtf"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        if path.lower().endswith(".pdf"):
            messagebox.showinfo(
                "PDF tip",
                "Plain-text extraction works best with .txt/.md.\n"
                "For PDF, paste key bullets into Extra context if text looks messy.",
            )
        self.resume_text = _read_text_file(path)
        self.resume_name.set(Path(path).name)

    def _start(self):
        cfg = {
            "resume": self.resume_text,
            "job_description": self.jd_box.get("1.0", "end").strip(),
            "extra": self.extra_box.get("1.0", "end").strip(),
            "model": self.model_var.get(),
            "language": self.lang_var.get(),
            "audio_mode": self.audio_var.get(),
            "auto_answer": bool(self.auto_answer_var.get()),
        }
        self.on_start(cfg)
