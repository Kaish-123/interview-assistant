"""Verify chat pane scrolls to end when reopening with saved history."""

from __future__ import annotations

import tkinter as tk


class _ScrollHarness:
    """Minimal stand-in for Application scroll helpers."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.response_box = tk.Text(root, height=8, width=40, wrap="word")
        self.response_box.pack()
        self._scroll_to_end_on_load = False

    def _scroll_response_to_end(self):
        try:
            self.response_box.see(tk.END)
            self.response_box.update_idletasks()
        except Exception:
            pass

    def _finish_startup_scroll(self):
        self._scroll_response_to_end()
        self._scroll_to_end_on_load = False

    def load_history(self, *, scroll_to_end: bool) -> None:
        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete("1.0", tk.END)
        if scroll_to_end:
            self._scroll_to_end_on_load = True
        for i in range(80):
            self.response_box.insert(
                tk.END,
                f"\n\n---------------------------------------------------------------------\n"
                f"QUESTION: Question {i}\n"
                f"------------------\nANSWER: Answer {i}\n",
            )
        self.response_box.config(state=tk.DISABLED)
        if scroll_to_end:
            self._scroll_response_to_end()
            self.root.after(300, self._finish_startup_scroll)


def _bottom_fraction(text: tk.Text) -> float:
    text.update_idletasks()
    return float(text.yview()[1])


def test_reopen_scrolls_to_end():
    root = tk.Tk()
    root.geometry("400x120")
    try:
        app = _ScrollHarness(root)
        app.load_history(scroll_to_end=True)
        root.update_idletasks()
        root.update()
        assert _bottom_fraction(app.response_box) >= 0.99
    finally:
        root.destroy()


def test_switch_chat_keeps_top_without_scroll_flag():
    root = tk.Tk()
    root.geometry("400x120")
    try:
        app = _ScrollHarness(root)
        app.load_history(scroll_to_end=False)
        root.update_idletasks()
        root.update()
        assert _bottom_fraction(app.response_box) < 0.99
    finally:
        root.destroy()
