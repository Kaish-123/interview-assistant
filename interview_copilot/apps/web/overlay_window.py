"""Native Live overlay — always-on-top, excluded from screen capture.

One window: controls on top, a single scrollable QUESTION/ANSWER log below
(same layout as the old tool). Spawned by the web companion so answers stay
on your display but are omitted from screen shares that honor capture-exclusion
(macOS NSWindowSharingNone, Windows WDA_EXCLUDEFROMCAPTURE).
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import traceback
import urllib.error
import urllib.request
from typing import Any

from interview_copilot.packages.stt.question_text import collapse_snowball, question_type_chunks


def _fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=2.5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=2.5) as resp:
        return json.loads(resp.read().decode("utf-8"))


MAIN_TITLE = "Live Assist"
CLOSE_TITLE = "Live Assist Close"

_ANSWER_PLACEHOLDERS = {
    "",
    "Listening — answers stream here.",
    "Answers appear here. This window is excluded from screen capture.",
}

_LOG_IDLE = (
    "Waiting for a question…\n\n"
    "Questions and answers stay in this pane. Scroll to review every turn."
)


def _last_role(messages: list[dict[str, Any]], role: str) -> str:
    for m in reversed(messages or []):
        if m.get("role") == role and m.get("content"):
            return str(m["content"])
    return ""


def overlay_qa_from_snapshot(snap: dict[str, Any]) -> tuple[str, str]:
    """Question + answer for the overlay, preferring live tab state over chat history."""
    messages = snap.get("messages") or []
    overlay_meta = (snap.get("meta") or {}).get("overlay") or {}
    question = (
        str(overlay_meta.get("transcript") or "").strip()
        or str(snap.get("last_question") or "").strip()
        or _last_role(messages, "user")
        or "Waiting for a question…"
    )
    answer = (
        str(overlay_meta.get("answer") or "").strip()
        or str(snap.get("partial") or "").strip()
        or str(snap.get("last_answer") or "").strip()
        or _last_role(messages, "assistant")
        or "Listening — answers stream here."
    )
    question = collapse_snowball(question)
    if not question:
        question = "Waiting for a question…"
    return question, answer


def _flatten_content(content: Any) -> str:
    if isinstance(content, list):
        bits: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                bits.append(str(item.get("text") or ""))
            elif isinstance(item, dict) and item.get("type") == "image_url":
                bits.append("[Image]")
            elif item:
                bits.append(str(item))
        return "\n".join(b for b in bits if b).strip()
    return str(content or "").strip()


def overlay_turns_from_snapshot(snap: dict[str, Any]) -> list[tuple[str, str]]:
    """Committed history, then the current question/answer appended at the bottom."""
    messages = snap.get("messages") or []
    overlay_meta = (snap.get("meta") or {}).get("overlay") or {}
    turns: list[tuple[str, str]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        text = _flatten_content(m.get("content"))
        if not text or role not in {"user", "assistant"}:
            continue
        turns.append((str(role), text))

    live_q = collapse_snowball(str(overlay_meta.get("transcript") or "").strip())
    live_a = (
        str(overlay_meta.get("answer") or "").strip()
        or str(snap.get("partial") or "").strip()
    )
    if live_a in _ANSWER_PLACEHOLDERS:
        live_a = ""

    if live_q:
        if turns and turns[-1][0] == "user":
            turns[-1] = ("user", live_q)
        else:
            last_user = next((t for _role, t in reversed(turns) if _role == "user"), "")
            if collapse_snowball(last_user) != live_q:
                turns.append(("user", live_q))
    if live_a:
        if turns and turns[-1][0] == "assistant":
            prev_a = turns[-1][1]
            if len(live_a) >= len(prev_a) or prev_a.startswith(live_a):
                turns[-1] = ("assistant", live_a)
        else:
            turns.append(("assistant", live_a))
    return turns


def overlay_log_from_snapshot(snap: dict[str, Any]) -> str:
    """Plain-text log matching the old tool: QUESTION / ANSWER blocks, all turns."""
    turns = overlay_turns_from_snapshot(snap)
    if not turns:
        return _LOG_IDLE
    parts: list[str] = []
    for role, text in turns:
        if role == "user":
            parts.append(f"QUESTION: {text}")
        else:
            parts.append(f"------------------\nANSWER: {text}")
    return "\n\n".join(parts)


def should_apply_answer(prev: str, nxt: str) -> bool:
    """Keep a stable pane: stream forward, never wipe/reprint a longer answer."""
    if nxt == prev:
        return False
    if nxt in _ANSWER_PLACEHOLDERS and prev and prev not in _ANSWER_PLACEHOLDERS:
        return False
    if prev and nxt and prev.startswith(nxt) and len(prev) > len(nxt) + 12:
        return False
    return True


def moved_geometry(cur_x: int, cur_y: int, dx: int, dy: int) -> str:
    return f"+{int(cur_x) + int(dx)}+{int(cur_y) + int(dy)}"


def close_chip_geometry(root_x: int, root_y: int, root_w: int) -> str:
    """Pin a tiny close button on the overlay's top-right corner."""
    x = max(8, int(root_x) + max(0, int(root_w) - 40))
    y = max(8, int(root_y) + 6)
    return f"36x28+{x}+{y}"


def run_overlay(base: str, engine_id: str) -> None:
    import tkinter as tk
    from tkinter import ttk

    from interview_copilot.platform.hotkeys import listen_toggle_hint, mono_font, overlay_close_hint, ui_font
    from interview_copilot.platform.privacy import (
        bring_app_to_front,
        exclude_tk_window_from_capture,
        hide_app_from_dock,
        hide_from_taskbar,
        overlay_start_geometry,
        set_click_through,
    )

    base = base.rstrip("/")
    root = tk.Tk()
    root.title(MAIN_TITLE)
    root.geometry(overlay_start_geometry(460, 640))
    root.minsize(340, 400)
    root.configure(bg="#121820")
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", 0.92)
    except tk.TclError:
        pass
    root.lift()
    root.update_idletasks()
    bring_app_to_front(root)
    exclude_tk_window_from_capture(root)
    hide_app_from_dock()
    hide_from_taskbar(root)

    click_through = {"on": False}
    poll_ok = {"n": 0}
    drag = {"x": 0, "y": 0}

    chrome = tk.Frame(root, bg="#0c1016", cursor="fleur")
    chrome.pack(fill="x")
    title_var = tk.StringVar(value="LIVE  ·  hidden from share")
    tk.Label(
        chrome,
        textvariable=title_var,
        fg="#8b9bb0",
        bg="#0c1016",
        font=ui_font(11, bold=True),
        cursor="fleur",
    ).pack(side="left", padx=10, pady=8)

    status = tk.StringVar(value="Connecting…")
    tk.Label(chrome, textvariable=status, fg="#6ee7b7", bg="#0c1016", font=ui_font(10), cursor="fleur").pack(
        side="right", padx=10
    )

    btns = tk.Frame(root, bg="#121820")
    btns.pack(fill="x", padx=8, pady=(6, 0))

    listen_var = tk.StringVar(value="Listen")
    stop_var = tk.StringVar(value="Stop & Process")
    overlay_state = {"listening": False}

    def send_cmd(command: str) -> None:
        try:
            _post_json(
                f"{base}/api/privacy/command",
                {"engine_id": engine_id, "command": command},
            )
            status.set(f"Sent {command}")
        except Exception as exc:
            status.set(str(exc)[:80])

    def start_listen_from_overlay() -> None:
        send_cmd("listen")
        overlay_state["listening"] = True
        listen_var.set("Listening…")

    def stop_listen_from_overlay() -> None:
        send_cmd("stop_listen")
        overlay_state["listening"] = False
        listen_var.set("Listen")

    ttk.Button(btns, textvariable=listen_var, command=lambda: send_cmd("toggle_listen")).pack(side="left", padx=2)
    ttk.Button(btns, textvariable=stop_var, command=stop_listen_from_overlay).pack(side="left", padx=2)
    ttk.Button(btns, text="Auto", command=lambda: send_cmd("auto_on")).pack(side="left", padx=2)
    ttk.Button(btns, text="Stop auto", command=lambda: send_cmd("auto_off")).pack(side="left", padx=2)
    ttk.Button(btns, text="Screen", command=lambda: send_cmd("screen")).pack(side="left", padx=2)

    ct_label = tk.StringVar(value="Click-through off")

    def apply_click_through(on: bool) -> bool:
        return set_click_through(root, on, title=MAIN_TITLE)

    def refresh_ct_ui() -> None:
        on = click_through["on"]
        ct_label.set("Turn click-through OFF" if on else "Click-through off")
        title_var.set(
            "LIVE  ·  click-through on — red × still closes"
            if on
            else "LIVE  ·  hidden from share  ·  drag the top bar"
        )

    def toggle_click_through(_event=None) -> None:
        click_through["on"] = not click_through["on"]
        ok = apply_click_through(click_through["on"])
        refresh_ct_ui()
        if not ok:
            status.set("Click-through unavailable")
        elif click_through["on"]:
            status.set("Click-through on — use the red × to close")
            _keep_chip_clickable()
        else:
            status.set("Click-through off")

    def on_close() -> None:
        try:
            chip.destroy()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
        os._exit(0)

    ttk.Button(btns, textvariable=ct_label, command=toggle_click_through).pack(side="left", padx=2)
    ttk.Button(btns, text="Close", command=on_close).pack(side="right", padx=2)
    tk.Label(
        btns,
        text=f"{overlay_close_hint()}   ·   {listen_toggle_hint()}",
        fg="#8b9bb0",
        bg="#121820",
        font=ui_font(9),
    ).pack(side="right", padx=6)

    chip = tk.Toplevel(root)
    chip.title(CLOSE_TITLE)
    try:
        chip.overrideredirect(True)
    except tk.TclError:
        pass
    chip.configure(bg="#c23b3b")
    chip.attributes("-topmost", True)
    chip.resizable(False, False)
    exclude_tk_window_from_capture(chip)
    tk.Button(
        chip,
        text="×",
        command=on_close,
        bg="#c23b3b",
        fg="#ffffff",
        activebackground="#a12e2e",
        activeforeground="#ffffff",
        relief="flat",
        font=ui_font(13, bold=True),
        padx=4,
        pady=0,
        cursor="hand2",
        highlightthickness=0,
        borderwidth=0,
    ).pack(fill="both", expand=True)

    def _keep_chip_clickable() -> None:
        try:
            set_click_through(chip, False, title=CLOSE_TITLE)
        except Exception:
            pass

    def place_chip() -> None:
        try:
            if not root.winfo_exists() or not chip.winfo_exists():
                return
            root.update_idletasks()
            chip.geometry(
                close_chip_geometry(root.winfo_rootx(), root.winfo_rooty(), root.winfo_width())
            )
            chip.lift()
            chip.attributes("-topmost", True)
            _keep_chip_clickable()
        except tk.TclError:
            return
        root.after(400, place_chip)

    def _start_drag(event) -> None:
        if click_through["on"]:
            return
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    def _on_drag(event) -> None:
        if click_through["on"]:
            return
        dx = event.x_root - drag["x"]
        dy = event.y_root - drag["y"]
        drag["x"] = event.x_root
        drag["y"] = event.y_root
        try:
            root.geometry(moved_geometry(root.winfo_x(), root.winfo_y(), dx, dy))
        except tk.TclError:
            pass

    for widget in (chrome, *chrome.winfo_children()):
        widget.bind("<Button-1>", _start_drag)
        widget.bind("<B1-Motion>", _on_drag)

    log_frame = tk.Frame(root, bg="#121820")
    log_frame.pack(fill="both", expand=True, padx=8, pady=(8, 6))
    scroll = tk.Scrollbar(log_frame)
    scroll.pack(side="right", fill="y")
    answer = tk.Text(
        log_frame,
        bg="#0f1419",
        fg="#e8eef6",
        insertbackground="#e8eef6",
        font=mono_font(12),
        wrap="word",
        relief="flat",
        highlightthickness=0,
        padx=12,
        pady=10,
        yscrollcommand=scroll.set,
    )
    answer.pack(side="left", fill="both", expand=True)
    scroll.config(command=answer.yview)
    answer.tag_configure("q", foreground="#7ec8ff")
    answer.tag_configure("a", foreground="#e8eef6")
    answer.tag_configure("meta", foreground="#8b9bb0")
    answer.insert("1.0", _LOG_IDLE, "meta")
    answer.configure(state="disabled")

    foot = tk.Frame(root, bg="#121820")
    foot.pack(fill="x", padx=8, pady=(0, 8))
    tk.Label(foot, text="Opacity", fg="#8b9bb0", bg="#121820", font=ui_font(10)).pack(side="left")
    opacity = tk.DoubleVar(value=82)

    def apply_opacity(_event=None) -> None:
        try:
            root.attributes("-alpha", max(0.25, min(1.0, opacity.get() / 100.0)))
        except tk.TclError:
            pass

    tk.Scale(
        foot,
        from_=25,
        to=100,
        orient="horizontal",
        variable=opacity,
        showvalue=False,
        command=lambda _v: apply_opacity(),
        bg="#121820",
        fg="#8b9bb0",
        highlightthickness=0,
        troughcolor="#1c2430",
        length=140,
    ).pack(side="left", padx=8)

    last_text = {"log": "", "shown": ""}
    type_job: dict[str, Any] = {"after": None, "queue": []}

    def _fill_log(text: str) -> None:
        answer.delete("1.0", "end")
        chunks = text.split("\n\n")
        for i, chunk in enumerate(chunks):
            if chunk.startswith("QUESTION:"):
                tag = "q"
            elif chunk.startswith("------------------") or chunk.startswith("ANSWER:"):
                tag = "a"
            else:
                tag = "meta"
            answer.insert("end", chunk, tag)
            if i < len(chunks) - 1:
                answer.insert("end", "\n\n")

    def _insert_chunk(chunk: str, tag: str) -> None:
        answer.configure(state="normal")
        answer.insert("end", chunk, tag)
        answer.configure(state="disabled")
        last_text["shown"] = last_text["shown"] + chunk
        try:
            answer.see("end")
        except Exception:
            pass

    def _suffix_tag(prev: str) -> str:
        qi = prev.rfind("QUESTION:")
        ai = prev.rfind("ANSWER:")
        return "a" if ai > qi else "q"

    def _pump_type() -> None:
        type_job["after"] = None
        if not type_job["queue"]:
            return
        chunk, tag = type_job["queue"].pop(0)
        _insert_chunk(chunk, tag)
        if type_job["queue"]:
            type_job["after"] = root.after(42, _pump_type)

    def _cancel_type() -> None:
        type_job["queue"].clear()
        if type_job["after"] is not None:
            try:
                root.after_cancel(type_job["after"])
            except Exception:
                pass
            type_job["after"] = None

    def _enqueue_suffix(suffix: str, tag: str) -> None:
        if not suffix:
            return
        if "\n" in suffix or "ANSWER:" in suffix or suffix.count(" ") <= 1:
            _insert_chunk(suffix, tag)
            return
        type_job["queue"].extend((c, tag) for c in question_type_chunks(suffix))
        if type_job["after"] is None:
            _pump_type()

    def set_log(text: str) -> None:
        if text == last_text["log"]:
            return
        last_text["log"] = text
        displayed = last_text["shown"]
        if displayed and text.startswith(displayed) and displayed != _LOG_IDLE:
            _cancel_type()
            _enqueue_suffix(text[len(displayed) :], _suffix_tag(displayed))
            return
        _cancel_type()
        answer.configure(state="normal")
        if text.startswith("QUESTION:") and (not displayed or displayed == _LOG_IDLE):
            answer.delete("1.0", "end")
            answer.insert("end", "QUESTION: ", "q")
            last_text["shown"] = "QUESTION: "
            answer.configure(state="disabled")
            _enqueue_suffix(text[len("QUESTION: ") :], "q")
            return
        _fill_log(text)
        last_text["shown"] = text
        answer.configure(state="disabled")
        try:
            answer.see("end")
        except Exception:
            pass

    def poll() -> None:
        try:
            snap = _fetch_json(f"{base}/api/engines/{engine_id}")
            set_log(overlay_log_from_snapshot(snap))
            overlay_meta = (snap.get("meta") or {}).get("overlay") or {}
            listening = bool(overlay_meta.get("listening"))
            overlay_state["listening"] = listening
            listen_var.set("Listening…" if listening else "Listen")
            if click_through["on"]:
                status.set("Click-through on — use the red × to close")
                apply_click_through(True)
                _keep_chip_clickable()
            else:
                st = overlay_meta.get("status") or "Hidden from share"
                status.set(str(st)[:48])
            poll_ok["n"] += 1
            if poll_ok["n"] % 12 == 1:
                exclude_tk_window_from_capture(root)
                exclude_tk_window_from_capture(chip)
                if click_through["on"]:
                    apply_click_through(True)
                    _keep_chip_clickable()
        except urllib.error.HTTPError as exc:
            status.set(f"Engine {exc.code}")
            if exc.code == 404:
                set_log("Session ended. Click Close.")
        except Exception as exc:
            status.set(str(exc)[:60])
        root.after(120, poll)

    def _on_term(_signum, _frame) -> None:
        os._exit(0)

    signal.signal(signal.SIGTERM, _on_term)
    try:
        signal.signal(signal.SIGINT, _on_term)
    except Exception:
        pass
    root.protocol("WM_DELETE_WINDOW", on_close)
    chip.protocol("WM_DELETE_WINDOW", on_close)
    root.bind("<Command-Shift-o>", toggle_click_through)
    root.bind("<Control-Shift-o>", toggle_click_through)
    root.bind("<Command-Shift-w>", lambda e: on_close())
    root.bind("<Control-Shift-w>", lambda e: on_close())
    root.bind("<Escape>", lambda e: toggle_click_through() if click_through["on"] else None)
    root.bind("<Command-minus>", lambda e: (opacity.set(max(25, opacity.get() - 8)), apply_opacity()))
    root.bind("<Command-equal>", lambda e: (opacity.set(min(100, opacity.get() + 8)), apply_opacity()))
    root.bind("<Control-minus>", lambda e: (opacity.set(max(25, opacity.get() - 8)), apply_opacity()))
    root.bind("<Control-equal>", lambda e: (opacity.set(min(100, opacity.get() + 8)), apply_opacity()))
    root.after(200, lambda: exclude_tk_window_from_capture(root))
    root.after(220, place_chip)
    root.after(250, poll)
    root.mainloop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture-excluded Live overlay")
    parser.add_argument("--engine-id", required=True)
    parser.add_argument("--base", default="http://127.0.0.1:8787")
    args = parser.parse_args(argv)
    if sys.platform not in {"darwin", "win32"}:
        print("Native hide-from-share overlay runs on macOS and Windows.", file=sys.stderr)
        return 2
    try:
        run_overlay(args.base, args.engine_id)
    except Exception:
        from interview_copilot.shared.config.paths import get_paths

        log = get_paths().logs_dir / "overlay.log"
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
