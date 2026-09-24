"""Bookmark panel helpers for Studio (persisted via ChatHistoryStore)."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional


class BookmarkController:
    def __init__(
        self,
        listbox: tk.Listbox,
        response_box: tk.Text,
        *,
        on_change: Callable[[], None],
        status: Callable[[str], None],
    ):
        self.listbox = listbox
        self.response_box = response_box
        self.on_change = on_change
        self.status = status
        self.bookmarks: list[tuple[str, str]] = []  # (line_index, preview)
        self.cursor = -1
        self.listbox.bind("<<ListboxSelect>>", self._on_click)
        self.listbox.bind("<Double-Button-1>", self._on_delete)

    def clear(self) -> None:
        self.bookmarks.clear()
        self.listbox.delete(0, tk.END)
        self.cursor = -1
        try:
            self.response_box.tag_remove("bookmark_highlight", "1.0", tk.END)
        except Exception:
            pass

    def load(self, entries: list) -> None:
        self.clear()
        for entry in entries or []:
            if len(entry) < 2:
                continue
            idx, preview = str(entry[0]), str(entry[1])
            self.bookmarks.append((idx, preview))
            self.listbox.insert(tk.END, f"Q{len(self.bookmarks)}")
            self._highlight(idx)

    def as_persistable(self) -> list[list[str]]:
        return [[idx, preview] for idx, preview in self.bookmarks]

    def add_at_cursor(self) -> None:
        try:
            visible = self.response_box.index("@0,0")
            pos = self.response_box.search("QUESTION:", visible, backwards=True, stopindex="1.0")
            if not pos:
                pos = self.response_box.search("QUESTION:", visible, forwards=True, stopindex=tk.END)
            if not pos:
                pos = visible
                preview = "📍 Manual mark"
            else:
                line_end = f"{pos.split('.')[0]}.end"
                preview = self.response_box.get(pos, line_end).strip()
                if len(preview) > 40:
                    preview = preview[:37] + "..."
            self._add(pos, preview)
        except Exception as e:
            self.status(f"Bookmark error: {e}")

    def go_next(self) -> None:
        if not self.bookmarks:
            self.status("No bookmarks — add with F4 / 🔖")
            return
        self.cursor = (self.cursor + 1) % len(self.bookmarks)
        idx, preview = self.bookmarks[self.cursor]
        self.response_box.see(idx)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.cursor)
        self.status(f"Bookmark {self.cursor + 1}/{len(self.bookmarks)}: {preview[:40]}")

    def _add(self, line_index: str, preview: str) -> None:
        line_num = line_index.split(".")[0]
        for existing, _ in self.bookmarks:
            if existing.split(".")[0] == line_num:
                self.status("Line already bookmarked")
                return
        self.bookmarks.append((line_index, preview))
        self.listbox.insert(tk.END, f"Q{len(self.bookmarks)}")
        self._highlight(line_index)
        self.status(f"Bookmark #{len(self.bookmarks)} added")
        self.on_change()

    def _highlight(self, line_index: str) -> None:
        try:
            line_num = line_index.split(".")[0]
            self.response_box.config(state=tk.NORMAL)
            self.response_box.tag_add("bookmark_highlight", f"{line_num}.0", f"{line_num}.end")
            self.response_box.config(state=tk.DISABLED)
        except Exception:
            pass

    def _on_click(self, _event=None) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        i = sel[0]
        if i < len(self.bookmarks):
            self.cursor = i
            idx, preview = self.bookmarks[i]
            self.response_box.see(idx)
            self.status(f"Jumped to: {preview[:40]}")

    def _on_delete(self, _event=None) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        i = sel[0]
        if i >= len(self.bookmarks):
            return
        idx, preview = self.bookmarks[i]
        try:
            line_num = idx.split(".")[0]
            self.response_box.config(state=tk.NORMAL)
            self.response_box.tag_remove("bookmark_highlight", f"{line_num}.0", f"{line_num}.end")
            self.response_box.config(state=tk.DISABLED)
        except Exception:
            pass
        del self.bookmarks[i]
        self.listbox.delete(0, tk.END)
        for n, _ in enumerate(self.bookmarks):
            self.listbox.insert(tk.END, f"Q{n + 1}")
        self.status(f"Removed bookmark: {preview[:30]}")
        self.on_change()
