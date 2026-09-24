"""
Studio UI — Milestone 8 parity (P0 prototype features on packages).

Prompts sidebar, chat history, bookmarks, Fast/Full, model cycle,
screenshot/paste, always-on-top, font, default-interview queue, hotkeys.

Run:
  python3 -m interview_copilot.apps.studio
"""

from __future__ import annotations

import io
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Optional

from PIL import Image, ImageGrab

from interview_copilot.apps.studio.bookmarks import BookmarkController
from interview_copilot.packages.audio import AudioRecorder
from interview_copilot.packages.context import image_url_part
from interview_copilot.packages.llm import (
    InterviewLLMEngine,
    cycle_answer_mode,
    describe_answer_mode,
    label_answer_mode,
)
from interview_copilot.packages.prompts import PromptTabsStore, SetupProfilesStore
from interview_copilot.packages.session import (
    AUTO_SAVE_TITLE,
    ChatHistoryStore,
    UIPreferencesStore,
    prune_sessions,
)
from interview_copilot.shared.config import get_paths, get_settings
from interview_copilot.shared.logging import setup_logging

try:
    import pyautogui
except ImportError:  # pragma: no cover
    pyautogui = None  # type: ignore


class StudioWindow(tk.Tk):
    """Studio assistant with prototype P0 feature parity."""

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        setup_logging(self.settings)
        self.paths = get_paths()
        self.prefs = UIPreferencesStore(self.paths.ui_prefs_json)

        self.title("Interview Copilot — Studio")
        geom = self.prefs.get("geometry") or "1100x820"
        try:
            self.geometry(str(geom))
        except Exception:
            self.geometry("1100x820")
        self.minsize(900, 640)
        self.configure(bg="#1e1e1e")

        self.engine = InterviewLLMEngine(
            model=self.settings.llm.default_model,
            language=self.settings.default_language,
            settings=self.settings,
        )
        self.recorder = AudioRecorder(self.settings)
        self.chats = ChatHistoryStore(self.paths.chats_json)
        self.prompts = PromptTabsStore(self.paths.tabs_json)
        self.profiles = SetupProfilesStore(self.paths.setup_profiles_json)

        self._busy = False
        self._listening = False
        self._always_on_top = False
        self._font_size = int(self.prefs.get("response_font_size") or 12)
        self._current_chat_index = 0
        self._profile_queue: list[str] = []
        self._profile_name = ""
        self.pending_attachments: list[dict] = []
        self._subtab_sending = False
        self._hotkey_listener = None

        self.status_var = tk.StringVar(value="Ready")
        self.mode_var = tk.StringVar(value=f"Mode: {label_answer_mode(self.engine.answer_mode)}")
        self.opt_var = tk.StringVar(
            value="⚡ Fast" if self.engine.optimization_mode else "🐢 Full"
        )
        self.model_var = tk.StringVar(value=self._model_label(self.engine.model))
        self.audio_var = tk.StringVar(
            value="BlackHole" if self.recorder.input_mode == "internal" else "Mic"
        )

        self._restore_autosave()
        self._build()
        self._bind_hotkeys()
        self._start_global_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not self.settings.has_api_key:
            messagebox.showwarning(
                "API key missing",
                "OPENAI_API_KEY not found.\nCopy interview_copilot/env.example to .env",
            )

    # ── UI construction ─────────────────────────────────────────────────

    def _build(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        self._build_sidebar()
        self._build_main()

        sash = self.prefs.get("paned_sash")
        if sash is not None:
            try:
                self.after(50, lambda: self.paned.sashpos(0, int(sash)))
            except Exception:
                pass

    def _build_sidebar(self) -> None:
        side = ttk.Frame(self.paned, width=260)
        self.paned.add(side, weight=0)

        ttk.Label(side, text="📋 Prompts").pack(anchor="w", padx=6, pady=(8, 2))
        prompt_frame = ttk.Frame(side)
        prompt_frame.pack(fill="both", expand=True, padx=4)
        self.tab_tree = ttk.Treeview(prompt_frame, show="tree", selectmode="browse")
        self.tab_tree.pack(side="left", fill="both", expand=True)
        ps = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.tab_tree.yview)
        ps.pack(side="right", fill="y")
        self.tab_tree.configure(yscrollcommand=ps.set)
        self.tab_tree.bind("<<TreeviewSelect>>", self._on_tab_select)

        btn_row = ttk.Frame(side)
        btn_row.pack(fill="x", padx=4, pady=4)
        ttk.Button(btn_row, text="+ Tab", command=self._add_tab, width=8).pack(side="left", padx=1)
        ttk.Button(btn_row, text="+ Sub", command=self._add_subtab, width=8).pack(side="left", padx=1)
        ttk.Button(btn_row, text="📌 Default", command=self.apply_default_interview, width=10).pack(
            side="left", padx=1
        )

        ttk.Label(side, text="📁 Profiles (double-click)").pack(anchor="w", padx=6, pady=(6, 2))
        self.profile_list = tk.Listbox(side, height=4, font=("Menlo", 10))
        self.profile_list.pack(fill="x", padx=6)
        self.profile_list.bind("<Double-Button-1>", self._on_profile_double_click)

        ttk.Label(side, text="💬 Past chats").pack(anchor="w", padx=6, pady=(8, 2))
        chat_frame = ttk.Frame(side)
        chat_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.chat_tree = ttk.Treeview(chat_frame, show="tree", selectmode="browse")
        self.chat_tree.pack(side="left", fill="both", expand=True)
        cs = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_tree.yview)
        cs.pack(side="right", fill="y")
        self.chat_tree.configure(yscrollcommand=cs.set)
        self.chat_tree.bind("<<TreeviewSelect>>", self._on_chat_select)

        chat_btns = ttk.Frame(side)
        chat_btns.pack(fill="x", padx=4, pady=(0, 8))
        ttk.Button(chat_btns, text="Rename", command=self._rename_chat, width=8).pack(side="left", padx=1)
        ttk.Button(chat_btns, text="Delete others", command=self._delete_other_chats, width=12).pack(
            side="left", padx=1
        )

        self._reload_prompt_tree()
        self._reload_profiles()
        self._reload_chat_tree()

    def _build_main(self) -> None:
        main = ttk.Frame(self.paned)
        self.paned.add(main, weight=1)

        # Toolbar row 1
        row1 = ttk.Frame(main)
        row1.pack(fill="x", padx=8, pady=(8, 2))
        self.listen_btn = ttk.Button(row1, text="🎤 Listen", command=self.toggle_listen, width=16)
        self.listen_btn.pack(side="left", padx=2)
        ttk.Button(row1, text="⏹ Stop", command=self.stop_output, width=8).pack(side="left", padx=2)
        ttk.Button(row1, text="🆕 New", command=self.start_new_chat, width=8).pack(side="left", padx=2)
        ttk.Button(row1, text="📁 Attach", command=self.attach_document, width=10).pack(side="left", padx=2)
        ttk.Button(row1, text="📸 Screen", command=self.capture_screenshot, width=10).pack(side="left", padx=2)
        ttk.Label(row1, textvariable=self.status_var).pack(side="right", padx=4)

        # Toolbar row 2
        row2 = ttk.Frame(main)
        row2.pack(fill="x", padx=8, pady=2)
        ttk.Button(row2, textvariable=self.model_var, command=self.toggle_model, width=10).pack(
            side="left", padx=2
        )
        ttk.Button(row2, textvariable=self.mode_var, command=self.toggle_mode, width=14).pack(
            side="left", padx=2
        )
        ttk.Button(row2, textvariable=self.opt_var, command=self.toggle_optimization, width=8).pack(
            side="left", padx=2
        )
        ttk.Button(row2, textvariable=self.audio_var, command=self.toggle_audio_mode, width=10).pack(
            side="left", padx=2
        )
        ttk.Button(row2, text="🔖", command=lambda: self.bookmarks.add_at_cursor(), width=3).pack(
            side="left", padx=2
        )
        ttk.Button(row2, text="A+", command=self.increase_font, width=3).pack(side="left", padx=1)
        ttk.Button(row2, text="A-", command=self.decrease_font, width=3).pack(side="left", padx=1)
        ttk.Button(row2, text="📌", command=self.toggle_topmost, width=3).pack(side="right", padx=2)
        ttk.Button(row2, text="💾", command=self.save_ui_prefs, width=3).pack(side="right", padx=2)

        # Response + bookmarks
        text_frame = ttk.Frame(main)
        text_frame.pack(fill="both", expand=True, padx=8, pady=4)

        bm_frame = ttk.Frame(text_frame, width=36)
        bm_frame.pack(side="right", fill="y")
        bm_frame.pack_propagate(False)
        ttk.Label(bm_frame, text="📍").pack()
        self.bookmark_list = tk.Listbox(
            bm_frame, width=4, bg="#2d2d30", fg="#ffd700",
            selectbackground="#4a4a00", font=("Arial", 9),
            highlightthickness=0, borderwidth=0,
        )
        self.bookmark_list.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(text_frame)
        scroll.pack(side="right", fill="y")
        self.response_box = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Menlo", self._font_size),
            bg="#252526",
            fg="#e8e8e8",
            insertbackground="white",
            highlightthickness=0,
            state=tk.DISABLED,
            yscrollcommand=scroll.set,
        )
        self.response_box.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.response_box.yview)
        self.response_box.tag_configure("meta", foreground="#9cdcfe")
        self.response_box.tag_configure("q", foreground="#7ec8ff")
        self.response_box.tag_configure("a", foreground="#e8e8e8")
        self.response_box.tag_configure("rule", foreground="#3d4d63")
        self.response_box.tag_configure("bookmark_highlight", background="#4a4a00", foreground="#ffff00")

        self.bookmarks = BookmarkController(
            self.bookmark_list,
            self.response_box,
            on_change=self._persist_bookmarks,
            status=lambda s: self.status_var.set(s),
        )

        # Input
        bottom = ttk.Frame(main)
        bottom.pack(fill="x", padx=8, pady=(4, 10))
        self.input_entry = tk.Text(
            bottom, height=3, wrap="word", font=("Menlo", 12),
            bg="#1e1e1e", fg="#e8e8e8", insertbackground="white",
            relief="solid", borderwidth=1,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.bind("<Shift-Return>", self._on_shift_enter)
        self.input_entry.bind("<Command-v>", self.handle_paste)
        self.input_entry.bind("<Control-v>", self.handle_paste)
        ttk.Button(bottom, text="Send ➡️", command=self.submit_text, width=10).pack(side="right")

        if any(
            isinstance(m, dict) and m.get("role") in ("user", "assistant")
            for m in self.engine.messages
        ):
            self._display_history()
            auto = self.chats.find_autosave()
            if auto:
                # find autosave index
                for i, s in enumerate(self.chats.sessions):
                    if s.get("title") == AUTO_SAVE_TITLE:
                        self._current_chat_index = i
                        self.bookmarks.load(self.chats.get_session_bookmarks(i))
                        break
        else:
            self._append("🤖 Studio ready — Listen, type, or pick a prompt.\n", tag="meta")

    def _bind_hotkeys(self) -> None:
        self.bind("<Command-Shift-i>", lambda e: self.apply_default_interview())
        self.bind("<Control-Shift-i>", lambda e: self.apply_default_interview())
        self.bind("<F4>", lambda e: self.bookmarks.add_at_cursor())
        self.bind("<Command-b>", lambda e: self.bookmarks.add_at_cursor())
        self.bind("<Control-b>", lambda e: self.bookmarks.add_at_cursor())
        self.bind("<F5>", lambda e: self.bookmarks.go_next())
        self.bind("<F2>", lambda e: self.save_ui_prefs())
        self.bind("<Command-equal>", lambda e: self.increase_font())
        self.bind("<Control-equal>", lambda e: self.increase_font())
        self.bind("<Command-minus>", lambda e: self.decrease_font())
        self.bind("<Control-minus>", lambda e: self.decrease_font())
        self.bind("<Command-p>", lambda e: self.toggle_topmost())
        self.bind("<grave>", self._on_grave)  # fallback if OS-global hotkeys fail
        self.bind("<asciitilde>", lambda e: self.stop_output())  # ~

    def _on_grave(self, _event=None):
        self.toggle_listen()
        return "break"

    def _start_global_hotkeys(self) -> None:
        """OS-global `` ` `` even when Studio is not focused. Failures are non-fatal."""
        try:
            from interview_copilot.platform.hotkeys import start_global_listen_hotkeys

            self._hotkey_listener = start_global_listen_hotkeys(
                on_listen_toggle=lambda: self.after(0, self.toggle_listen),
                on_stop=lambda: self.after(0, self.stop_output),
                on_screenshot=lambda: self.after(0, self.capture_screenshot),
            )
            if self._hotkey_listener is not None:
                self.unbind("<grave>")
        except Exception as e:
            self.status_var.set(f"Global hotkeys unavailable: {e}")

    # ── Sidebar data ────────────────────────────────────────────────────

    def _reload_prompt_tree(self) -> None:
        self.tab_tree.delete(*self.tab_tree.get_children())
        for i in range(self.prompts.get_tab_count()):
            tid = self.tab_tree.insert("", "end", text=self.prompts.get_tab_name(i), iid=f"tab_{i}")
            for j in range(self.prompts.get_subtab_count(i)):
                self.tab_tree.insert(
                    tid, "end", text=self.prompts.get_subtab_name(i, j), iid=f"sub_{i}_{j}"
                )

    def _reload_profiles(self) -> None:
        self.profile_list.delete(0, tk.END)
        for name in self.profiles.list_names():
            self.profile_list.insert(tk.END, name)

    def _reload_chat_tree(self) -> None:
        self.chat_tree.delete(*self.chat_tree.get_children())
        for i, title in enumerate(self.chats.get_titles()):
            self.chat_tree.insert("", "end", iid=f"chat_{i}", text=title)

    def _add_tab(self) -> None:
        name = simpledialog.askstring("New Tab", "Tab name:")
        if name:
            self.prompts.add_tab(name)
            self._reload_prompt_tree()

    def _add_subtab(self) -> None:
        sel = self.tab_tree.selection()
        if not sel:
            messagebox.showwarning("Select a tab", "Select a tab first")
            return
        item = sel[0]
        if item.startswith("sub_"):
            item = self.tab_tree.parent(item)
        if not item.startswith("tab_"):
            return
        tab_index = int(item.split("_")[1])
        name = simpledialog.askstring("New Subtab", "Name:")
        if not name:
            return
        prompt = simpledialog.askstring("Prompt", "Prompt / text:") or ""
        self.prompts.add_subtab(tab_index, name, prompt=prompt, text_input=prompt)
        self._reload_prompt_tree()

    def _on_tab_select(self, _event=None) -> None:
        if self._subtab_sending or self._busy:
            return
        sel = self.tab_tree.selection()
        if not sel:
            return
        item = sel[0]
        if not item.startswith("sub_"):
            return
        parts = item.split("_")
        t, s = int(parts[1]), int(parts[2])
        body = self.prompts.get_subtab_body(t, s).strip()
        if not body:
            return
        current = self.input_entry.get("1.0", tk.END).strip()
        if current:
            body = f"{current}\n\n{body}"
        self.input_entry.delete("1.0", tk.END)
        try:
            self._subtab_sending = True
            self.input_entry.insert("1.0", body)
            self.submit_text()
        finally:
            self._subtab_sending = False

    def _on_profile_double_click(self, _event=None) -> None:
        sel = self.profile_list.curselection()
        if not sel:
            return
        name = self.profile_list.get(sel[0])
        ids = self.profiles.load().get(name) or []
        self.apply_profile_ids(ids, profile_name=name)

    def apply_default_interview(self) -> None:
        ids = self.prefs.get("default_interview_subtabs") or []
        if not ids:
            # If none saved, offer to save current selection / first tab prompts
            messagebox.showinfo(
                "No default set",
                "Save default_interview_subtabs in ui_prefs, or create a profile.\n"
                "Tip: add prompts, then use a profile double-click.\n"
                "To set default: store subtab ids via prefs (Milestone UI) — "
                "for now applying first tab's subtabs if present.",
            )
            if self.prompts.get_tab_count() == 0:
                return
            ids = [
                self.prompts.subtab_id(0, j)
                for j in range(self.prompts.get_subtab_count(0))
            ]
            if ids:
                self.prefs.set_default_interview_subtabs(ids)
        self.apply_profile_ids(ids, profile_name="Default interview")

    def apply_profile_ids(self, subtab_ids: list[str], profile_name: str = "Profile") -> None:
        # Intro first
        intro, other = [], []
        for sid in subtab_ids:
            resolved = self.prompts.resolve_subtab_id(sid)
            if not resolved:
                continue
            name = (self.prompts.get_subtab_name(*resolved) or "").strip().lower()
            (intro if name == "intro" else other).append(sid)
        ordered = intro + other
        if not ordered:
            self.status_var.set("No valid prompts in profile")
            return
        self._profile_queue = list(ordered)
        self._profile_name = profile_name
        self._append(f"\n🚀 {profile_name}: {len(ordered)} prompts (one-by-one)\n", tag="meta")
        self._send_next_profile_prompt()

    def _send_next_profile_prompt(self) -> None:
        if not self._profile_queue:
            self.status_var.set(f"✅ {self._profile_name}: done")
            return
        if self._busy:
            self.after(400, self._send_next_profile_prompt)
            return
        sid = self._profile_queue.pop(0)
        combined, names = self.prompts.combined_prompt_for_ids([sid])
        if not combined:
            self.after(0, self._send_next_profile_prompt)
            return
        name = names[0] if names else sid
        self.status_var.set(f"{self._profile_name}: {name} ({len(self._profile_queue)} left)")
        self._run_answer(combined, on_complete=self._send_next_profile_prompt)

    def _on_chat_select(self, _event=None) -> None:
        sel = self.chat_tree.selection()
        if not sel:
            return
        item = sel[0]
        if not item.startswith("chat_"):
            return
        # persist working chat
        if any(isinstance(m, dict) and m.get("role") == "user" for m in self.engine.messages):
            self._autosave()
        index = int(item.split("_")[1])
        self._current_chat_index = index
        self.engine.messages = self.chats.get_session(index)
        self._display_history()
        self.bookmarks.load(self.chats.get_session_bookmarks(index))
        titles = self.chats.get_titles()
        self.status_var.set(f"Loaded: {titles[index] if index < len(titles) else ''}")

    def _rename_chat(self) -> None:
        sel = self.chat_tree.selection()
        if not sel:
            return
        index = int(sel[0].split("_")[1])
        old = self.chats.get_titles()[index]
        new = simpledialog.askstring("Rename", "New name:", initialvalue=old)
        if new:
            self.chats.rename_session(index, new)
            self._reload_chat_tree()

    def _delete_other_chats(self) -> None:
        sel = self.chat_tree.selection()
        if not sel:
            messagebox.showwarning("Select chat", "Select the chat to KEEP")
            return
        keep = int(sel[0].split("_")[1])
        if not messagebox.askyesno("Delete others", "Delete all chats except selection + AutoSave?"):
            return
        prune_sessions(self.chats, max_chats=0, keep_index=keep)
        # prune with max_chats=0 and keep_index keeps only keep + autosave
        self._reload_chat_tree()
        self.status_var.set("Deleted other chats")

    # ── Persistence / display ───────────────────────────────────────────

    def _restore_autosave(self) -> None:
        auto = self.chats.find_autosave()
        if auto and isinstance(auto.get("messages"), list) and auto["messages"]:
            self.engine.messages = auto["messages"]
            self.status_var.set("Resumed AutoSave session")

    def _autosave(self) -> None:
        try:
            self.chats.save_current_session(
                self.engine.messages,
                title=AUTO_SAVE_TITLE,
                bookmarks=self.bookmarks.as_persistable() if hasattr(self, "bookmarks") else None,
            )
            prune_sessions(self.chats, max_chats=10)
            self._reload_chat_tree()
        except Exception as e:
            self.status_var.set(f"Autosave failed: {e}")

    def _persist_bookmarks(self) -> None:
        self.chats.update_session_bookmarks(
            self._current_chat_index, self.bookmarks.as_persistable()
        )

    def save_ui_prefs(self) -> None:
        try:
            sash = self.paned.sashpos(0)
        except Exception:
            sash = None
        self.prefs.save(
            {
                "geometry": self.geometry(),
                "paned_sash": sash,
                "response_font_size": self._font_size,
            }
        )
        self.status_var.set("Saved UI prefs")

    def _on_close(self) -> None:
        try:
            if self._listening:
                self.recorder.is_recording = False
                self.recorder.stop_recording(self.paths.logs_dir / "_discard_close.wav")
            self._autosave()
            self.save_ui_prefs()
            if self._hotkey_listener:
                self._hotkey_listener.stop()
        finally:
            self.destroy()

    def _at_bottom(self) -> bool:
        try:
            return float(self.response_box.yview()[1]) >= 0.97
        except Exception:
            return True

    def _append(self, text: str, *, tag: str | None = None, follow: bool | None = None) -> None:
        pin = True if tag in {"q", "a", "rule"} else (self._at_bottom() if follow is None else follow)
        self.response_box.config(state=tk.NORMAL)
        if tag:
            self.response_box.insert(tk.END, text, tag)
        else:
            self.response_box.insert(tk.END, text)
        self.response_box.config(state=tk.DISABLED)
        if pin or follow:
            self.response_box.see(tk.END)

    def _append_async(self, text: str, tag: str | None = None) -> None:
        self.after(0, lambda: self._append(text, tag=tag))

    def _set_status(self, text: str) -> None:
        self.after(0, lambda: self.status_var.set(text))

    def _display_history(self) -> None:
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete("1.0", tk.END)
        self.response_box.config(state=tk.DISABLED)
        for m in self.engine.messages:
            if not isinstance(m, dict):
                continue
            role, content = m.get("role"), m.get("content", "")
            if isinstance(content, list):
                content = "\n".join(
                    c.get("text", "[Image]")
                    if isinstance(c, dict) and c.get("type") == "text"
                    else "[Image]"
                    for c in content
                )
            if role == "user":
                self._append(f"\nQUESTION: {content}\n", tag="q", follow=False)
            elif role == "assistant":
                self._append("------------------\n", tag="rule", follow=False)
                self._append(f"ANSWER: {content}\n", tag="a", follow=False)
        self.response_box.see(tk.END)

    # ── Toolbar actions ─────────────────────────────────────────────────

    def _model_label(self, model: str) -> str:
        short = {
            "gpt-4o": "🧠 4o",
            "gpt-4o-mini": "⚡ Mini",
            "gpt-4.1": "4.1",
            "gpt-4.1-mini": "4.1m",
            "gpt-4-turbo": "🚀 Turbo",
        }
        return short.get(model, model[:10])

    def toggle_model(self) -> None:
        models = list(self.settings.llm.available_models)
        try:
            i = models.index(self.engine.model)
        except ValueError:
            i = 0
        self.engine.model = models[(i + 1) % len(models)]
        self.engine.llm.model = self.engine.model
        self.model_var.set(self._model_label(self.engine.model))
        self.status_var.set(f"Model: {self.engine.model}")

    def toggle_mode(self) -> None:
        mode = cycle_answer_mode(self.engine.answer_mode)
        self.engine.answer_mode = mode
        self.mode_var.set(f"Mode: {label_answer_mode(mode)}")
        self.status_var.set(f"Answer mode: {describe_answer_mode(mode)}")

    def toggle_optimization(self) -> None:
        on = self.engine.toggle_optimization_mode()
        self.opt_var.set("⚡ Fast" if on else "🐢 Full")
        self.status_var.set("Fast mode ON" if on else "Full context mode")

    def toggle_audio_mode(self) -> None:
        if self.recorder.input_mode == "internal":
            self.recorder.input_mode = "external"
            self.audio_var.set("Mic")
            self.status_var.set("Audio: External mic")
        else:
            self.recorder.input_mode = "internal"
            self.audio_var.set("BlackHole")
            self.status_var.set("Audio: BlackHole")

    def toggle_topmost(self) -> None:
        self._always_on_top = not self._always_on_top
        self.attributes("-topmost", self._always_on_top)
        self.status_var.set("Pinned" if self._always_on_top else "Unpinned")

    def increase_font(self) -> None:
        self._font_size = min(24, self._font_size + 1)
        self.response_box.config(font=("Menlo", self._font_size))

    def decrease_font(self) -> None:
        self._font_size = max(8, self._font_size - 1)
        self.response_box.config(font=("Menlo", self._font_size))

    def start_new_chat(self) -> None:
        if any(isinstance(m, dict) and m.get("role") == "user" for m in self.engine.messages):
            title = time.strftime("Studio %Y-%m-%d %H:%M:%S")
            self.chats.add_session(
                title, self.engine.messages, bookmarks=self.bookmarks.as_persistable()
            )
            prune_sessions(self.chats, max_chats=10)
        self.engine = InterviewLLMEngine(
            model=self.settings.llm.default_model,
            language=self.settings.default_language,
            settings=self.settings,
        )
        self.bookmarks.clear()
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete("1.0", tk.END)
        self.response_box.config(state=tk.DISABLED)
        self._append("🤖 New conversation started.\n", tag="meta")
        self._autosave()
        self._reload_chat_tree()
        self.status_var.set("New chat")

    def attach_document(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Attach documents",
            filetypes=[("Documents", "*.txt *.pdf *.docx *.md *.py *.json"), ("All", "*.*")],
        )
        for path in paths:
            ok, msg = self.engine.load_document(path)
            self.status_var.set(msg)
            if ok:
                self._append(f"\n📎 Attached: {Path(path).name}\n", tag="meta")
            else:
                messagebox.showwarning("Attach", msg)
        self._autosave()

    def capture_screenshot(self) -> None:
        if pyautogui is None:
            messagebox.showerror("Screenshot", "pyautogui not installed")
            return
        try:
            shot = pyautogui.screenshot()
            part = image_url_part(shot, fmt="png", max_size=1280)
            content: list[Any] = [
                {"type": "text", "text": "Please analyze this screenshot."},
                part,
            ]
            self._run_answer(content)
        except Exception as e:
            messagebox.showerror("Screenshot", str(e))

    def handle_paste(self, event=None):
        try:
            text = self.clipboard_get()
            if isinstance(text, str) and text.strip():
                self.input_entry.insert(tk.INSERT, text)
                return "break"
        except tk.TclError:
            pass
        try:
            image = ImageGrab.grabclipboard()
            if isinstance(image, Image.Image):
                self.pending_attachments.append(image_url_part(image, fmt="png", max_size=1280))
                n = len(self.pending_attachments)
                self.input_entry.insert(tk.INSERT, f" [📎 Image {n}] ")
                self.status_var.set(f"{n} image(s) attached")
                return "break"
        except Exception as e:
            self.status_var.set(f"Paste error: {e}")
        return None

    def stop_output(self) -> None:
        self.engine.cancel()
        self._busy = False
        self._profile_queue.clear()
        self.status_var.set("Stopped")
        self.listen_btn.config(state=tk.NORMAL)

    def _on_enter(self, event=None):
        self.submit_text()
        return "break"

    def _on_shift_enter(self, event=None):
        self.input_entry.insert(tk.INSERT, "\n")
        return "break"

    def submit_text(self) -> None:
        question = self.input_entry.get("1.0", tk.END).strip()
        self.input_entry.delete("1.0", tk.END)
        if question == "--":
            self.capture_screenshot()
            return
        if not question and not self.pending_attachments:
            return
        if self._busy:
            return
        if self.pending_attachments:
            content: list[Any] = []
            if question:
                content.append({"type": "text", "text": question})
            content.extend(self.pending_attachments)
            self.pending_attachments = []
            self._run_answer(content)
        else:
            self._run_answer(question)

    def toggle_listen(self) -> None:
        if self._busy and not self._listening:
            return
        if not self._listening:
            self._start_listen()
        else:
            self._stop_listen_and_process()

    def _start_listen(self) -> None:
        self._listening = True
        self.listen_btn.config(text="🛑 Stop & Process")
        self.status_var.set("Listening to internal audio…")
        self._append("\n🎙 Listening…\n", tag="meta", follow=True)
        try:
            if self.recorder.input_mode != "internal":
                self.recorder.input_mode = "internal"
                self.audio_var.set("BlackHole")
            self.recorder.start_recording()
        except Exception as e:
            self._listening = False
            self.listen_btn.config(text="🎤 Listen")
            messagebox.showerror("Audio", str(e))

    def _stop_listen_and_process(self) -> None:
        self._listening = False
        self.listen_btn.config(text="🎤 Listen", state=tk.DISABLED)
        self.status_var.set("Transcribing…")
        self._busy = True

        def worker():
            wav = self.paths.logs_dir / "studio_listen.wav"
            try:
                saved = self.recorder.stop_recording(wav)
                if not saved:
                    self._set_status("No speech captured")
                    self.after(0, lambda: self.listen_btn.config(state=tk.NORMAL))
                    self._busy = False
                    return
                text = self.engine.transcribe(saved)
                if not text or text.startswith("❌"):
                    self._set_status(text or "Empty transcription")
                    self.after(0, lambda: self.listen_btn.config(state=tk.NORMAL))
                    self._busy = False
                    return
                self.after(0, lambda: self._run_answer(text))
            except Exception as e:
                self._set_status(f"Listen error: {e}")
                self.after(0, lambda: self.listen_btn.config(state=tk.NORMAL))
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _run_answer(self, question: Any, on_complete=None) -> None:
        self._busy = True
        self.listen_btn.config(state=tk.DISABLED)
        flat = question
        if isinstance(question, list):
            flat = "\n".join(
                c.get("text", "[Image]") if isinstance(c, dict) and c.get("type") == "text" else "[Image]"
                for c in question
            )
        self._append(f"\nQUESTION: {flat}\n", tag="q")
        self._append("------------------\n", tag="rule")
        self._append("ANSWER: ", tag="a")
        self.status_var.set("Generating…")

        def worker():
            try:
                gen = self.engine.stream_answer(question)
                try:
                    while True:
                        delta = next(gen)
                        self._append_async(delta, tag="a")
                except StopIteration:
                    pass
                self._append_async("\n", tag="a")
                self.after(0, self._autosave)
                self._set_status("Ready")
            except Exception as e:
                self._append_async(f"\n❌ {e}\n", tag="meta")
                self._set_status(f"Error: {e}")
            finally:
                self._busy = False
                self.after(0, lambda: self.listen_btn.config(state=tk.NORMAL, text="🎤 Listen"))
                if on_complete:
                    self.after(500, on_complete)

        threading.Thread(target=worker, daemon=True).start()


def run_studio() -> None:
    StudioWindow().mainloop()


if __name__ == "__main__":
    run_studio()
