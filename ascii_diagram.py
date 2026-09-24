"""
Fit ASCII / box-drawing system-design diagrams to a character budget.

Tk Text with wrap=WORD breaks alignment inside boxes (spaces are wrap points).
This module detects diagram blocks and reflows them so every line is <= max_cols,
preserving column alignment within each panel. Wide left-to-right flowcharts
are split at whitespace seams and stacked top-down.
"""

from __future__ import annotations

import re
import textwrap as _textwrap
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

BoxRange = Tuple[int, int]  # inclusive line indices

# Box drawing, arrows, and a few block elements models commonly emit.
BOX_DRAWING = frozenset(
    "─━│┃┄┅┆┇┈┉┊┋"
    "┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛"
    "├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫"
    "┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻"
    "┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋"
    "═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬"
    "╭╮╯╰╱╲╳"
    "╴╵╶╷╸╹╺╻╼╽╾╿"
    "→←↑↓↔↕⇒⇐⇑⇓⇔"
    "►◄▲▼▶◀▾▴▸◂▷◁△▽"
    "■□▪▫●○◆◇★☆"
)

# Horizontal rules used as UI / markdown separators — not diagrams.
_HR_RE = re.compile(r"^[-_=\u2500\u2550]{6,}$")
_ASCII_BOX_EDGE_RE = re.compile(r"[+][-+=]{2,}[+]")
_ASCII_BOX_SIDES_RE = re.compile(r"^\s*\|.*\|\s*$")
_TREE_RE = re.compile(r"^\s{0,40}(?:\|(?:\s{2,}|$)|[|\\+]--|\s+\\|/)")
_ARROW_RE = re.compile(r"(?:-->|<--|==>|<==|->|<-|=>|<=|→|←|⇒|⇐)")
_FENCE_RE = re.compile(r"^\s*```")
_SKIP_PREFIXES = (
    "QUESTION:",
    "ANSWER:",
    "Live Question:",
    "---- QUESTION",
    "---- ANSWER",
)

CONTINUATION_LINES = ("", "  |", "  v", "")
MIN_COLS = 16


def estimate_char_columns(widget_width_px: int, font_size: int, padding_px: int = 10) -> int:
    """Approximate how many Consolas-width columns fit in a widget."""
    char_w = max(1, int(round(float(font_size) * 0.60)))
    inner = max(1, int(widget_width_px) - int(padding_px))
    return max(MIN_COLS, inner // char_w)


def _expand(line: str) -> str:
    return line.expandtabs(4).rstrip("\n").rstrip()


def is_diagram_line(line: str) -> bool:
    """True if a line is structural ASCII/box art rather than wrapping prose."""
    raw = _expand(line)
    stripped = raw.strip()
    if not stripped:
        return False
    if _FENCE_RE.match(stripped):
        return False
    if any(stripped.startswith(p) for p in _SKIP_PREFIXES):
        return False
    if _HR_RE.match(stripped):
        return False
    if any(ch in BOX_DRAWING for ch in stripped):
        return True
    if _ASCII_BOX_EDGE_RE.search(stripped):
        return True
    if _ASCII_BOX_SIDES_RE.match(stripped) and len(stripped) >= 5:
        return True
    if stripped.startswith("|") and stripped.count("|") >= 2:
        # Markdown table row or ASCII column.
        return True
    if _TREE_RE.match(raw) and any(ch in "|+\\" for ch in stripped[:8]):
        return True
    arrows = _ARROW_RE.findall(stripped)
    if len(arrows) >= 2 and len(stripped) >= 10:
        return True
    if arrows and re.search(r"[+|]", stripped) and len(stripped) >= 8:
        return True
    # High density of structure chars (e.g. "    |         |    ").
    struct = sum(1 for ch in stripped if ch in "+-|/=\\<>^vV*")
    if len(stripped) >= 8 and struct / len(stripped) >= 0.45 and struct >= 4:
        return True
    return False


def is_arrow_flow_line(line: str) -> bool:
    stripped = _expand(line).strip()
    return len(_ARROW_RE.findall(stripped)) >= 2 and len(stripped) >= 10


def _fence_spans(lines: Sequence[str]) -> List[BoxRange]:
    spans: List[BoxRange] = []
    start: Optional[int] = None
    for i, ln in enumerate(lines):
        if _FENCE_RE.match(_expand(ln).strip()):
            if start is None:
                start = i
            else:
                spans.append((start, i))
                start = None
    return spans


def _mark_diagram_flags(lines: Sequence[str]) -> List[bool]:
    flags = [is_diagram_line(ln) for ln in lines]
    for start, end in _fence_spans(lines):
        body = lines[start + 1 : end]
        nonempty = [ln for ln in body if _expand(ln).strip()]
        if not nonempty:
            continue
        hits = sum(1 for ln in nonempty if is_diagram_line(ln) or is_arrow_flow_line(ln))
        if hits >= max(1, int(0.4 * len(nonempty))):
            for j in range(start, end + 1):
                flags[j] = True
    return flags


def find_diagram_blocks(lines: Sequence[str]) -> List[BoxRange]:
    """Inclusive (start, end) line ranges that should be reflowed together."""
    n = len(lines)
    flags = _mark_diagram_flags(lines)
    blocks: List[BoxRange] = []
    i = 0
    while i < n:
        if not flags[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < n:
            if flags[i]:
                i += 1
                continue
            # Allow a blank line inside a diagram (common between boxes).
            if not _expand(lines[i]).strip() and i + 1 < n and flags[i + 1]:
                i += 1
                continue
            break
        end = i - 1
        while end > start and not _expand(lines[end]).strip() and not flags[end]:
            end -= 1
        diagram_count = sum(1 for j in range(start, end + 1) if flags[j])
        single = start == end and is_arrow_flow_line(lines[start])
        if diagram_count >= 2 or single or (end > start and any(flags[start : end + 1])):
            if diagram_count >= 1:
                blocks.append((start, end))
        i = end + 1
    return blocks


def _dedent(lines: List[str]) -> List[str]:
    indents = []
    for ln in lines:
        if not ln.strip():
            continue
        if _FENCE_RE.match(ln.strip()):
            continue
        indents.append(len(ln) - len(ln.lstrip(" ")))
    if not indents:
        return list(lines)
    pad = min(indents)
    if pad <= 0:
        return list(lines)
    out = []
    for ln in lines:
        if not ln.strip():
            out.append("")
        elif _FENCE_RE.match(ln.strip()):
            out.append(ln.strip())
        else:
            out.append(ln[pad:] if len(ln) >= pad else ln)
    return out


def _space_column_runs(padded: Sequence[str], width: int) -> List[Tuple[int, int]]:
    runs: List[Tuple[int, int]] = []
    col = 0
    while col < width:
        if all(row[col] == " " for row in padded):
            begin = col
            while col < width and all(row[col] == " " for row in padded):
                col += 1
            runs.append((begin, col))
        else:
            col += 1
    return runs


def split_into_column_panels(lines: Sequence[str], max_cols: int) -> List[List[str]]:
    """Slice a 2D diagram at all-whitespace columns so each panel fits max_cols."""
    cleaned = [_expand(ln) for ln in lines]
    width = max((len(ln) for ln in cleaned), default=0)
    if width <= max_cols:
        return [cleaned]
    padded = [ln.ljust(width) for ln in cleaned]
    gaps = _space_column_runs(padded, width)
    panels: List[List[str]] = []
    start = 0
    while start < width:
        while start < width and all(row[start] == " " for row in padded):
            start += 1
        if start >= width:
            break
        target = start + max_cols
        if target >= width:
            panel = [row[start:].rstrip() for row in padded]
            if any(p.strip() for p in panel):
                panels.append(panel)
            break
        split_at = None
        next_start = target
        for gstart, gend in gaps:
            if start < gstart <= target:
                split_at = gstart
                next_start = max(gend, gstart)
            elif gstart > target:
                break
        if split_at is None:
            split_at = target
            next_start = target
        panel = [row[start:split_at].rstrip() for row in padded]
        if any(p.strip() for p in panel):
            panels.append(panel)
        if next_start <= start:
            next_start = start + max_cols
        start = next_start
    return panels or [cleaned]


def wrap_as_grid(lines: Sequence[str], max_cols: int) -> List[List[str]]:
    """Hard-slice a block into max_cols-wide vertical strips (last-resort)."""
    cleaned = [_expand(ln) for ln in lines]
    width = max((len(ln) for ln in cleaned), default=0)
    if width <= max_cols:
        return [cleaned]
    padded = [ln.ljust(width) for ln in cleaned]
    chunks: List[List[str]] = []
    for origin in range(0, width, max_cols):
        end = min(width, origin + max_cols)
        slice_rows = [row[origin:end].rstrip() for row in padded]
        if any(r.strip() for r in slice_rows):
            chunks.append(slice_rows)
    return chunks or [cleaned]


def stack_panels(panels: Sequence[Sequence[str]]) -> List[str]:
    if not panels:
        return []
    if len(panels) == 1:
        return list(panels[0])
    out: List[str] = []
    for i, panel in enumerate(panels):
        if i:
            out.extend(CONTINUATION_LINES)
        out.extend(panel)
    return out


# ---------------------------------------------------------------------------
# Box-aware reflow: keep components intact, wrap the chain to the window.
# ---------------------------------------------------------------------------

_TOP_LEFT = frozenset("┌╔╭┏")
_TOP_RIGHT = frozenset("┐╗╮┓")
_BOT_LEFT = frozenset("└╚╰┗")
_BOT_RIGHT = frozenset("┘╝╯┛")
_H_EDGE = frozenset("─━═┬╥┳")
_V_EDGE = frozenset("│┃║├┤╠╣╟╢")
_H_ARROW = "────▶"
_ASCII_H_ARROW = "---->"


@dataclass
class _Box:
    r0: int
    r1: int
    c0: int
    c1: int
    snippet: List[str]
    style: str  # "unicode" | "ascii"

    @property
    def width(self) -> int:
        return self.c1 - self.c0 + 1


def _pad_block(lines: Sequence[str]) -> Tuple[List[str], int]:
    cleaned = [_expand(ln) for ln in lines]
    width = max((len(ln) for ln in cleaned), default=0)
    return [ln.ljust(width) for ln in cleaned], width


def _inner_text(snippet: Sequence[str]) -> str:
    parts: List[str] = []
    for ln in snippet[1:-1]:
        if len(ln) >= 2:
            parts.append(ln[1:-1].strip())
        else:
            parts.append(ln.strip())
    return " ".join(p for p in parts if p)


def redraw_box(text: str, inner_width: int, style: str) -> List[str]:
    """Rebuild a box so its total width is inner_width + 2."""
    inner_width = max(3, int(inner_width))
    chunks = _textwrap.wrap(text, width=inner_width) or [""]
    if style == "ascii":
        top = "+" + "-" * inner_width + "+"
        bot = "+" + "-" * inner_width + "+"
        mid = ["|" + chunk.ljust(inner_width)[:inner_width] + "|" for chunk in chunks]
    else:
        top = "┌" + "─" * inner_width + "┐"
        bot = "└" + "─" * inner_width + "┘"
        mid = ["│" + chunk.ljust(inner_width)[:inner_width] + "│" for chunk in chunks]
    return [top, *mid, bot]


def shrink_box_snippet(snippet: Sequence[str], max_cols: int, style: str) -> List[str]:
    snip = [_expand(ln) for ln in snippet]
    width = max((len(ln) for ln in snip), default=0)
    if width <= max_cols and width >= 3:
        return [ln.ljust(width) for ln in snip]
    inner = max(3, max_cols - 2)
    return redraw_box(_inner_text(snip) or "?", inner, style)


def extract_boxes(lines: Sequence[str]) -> List[_Box]:
    """Find unicode and ASCII rectangles in a diagram block."""
    padded, width = _pad_block(lines)
    height = len(padded)
    used = [[False] * width for _ in range(height)] if width else []
    boxes: List[_Box] = []

    def take(r0: int, r1: int, c0: int, c1: int, style: str) -> None:
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                used[rr][cc] = True
        snippet = [padded[rr][c0 : c1 + 1] for rr in range(r0, r1 + 1)]
        boxes.append(_Box(r0, r1, c0, c1, snippet, style))

    for r in range(height):
        row = padded[r]
        for c, ch in enumerate(row):
            if width and used[r][c]:
                continue
            if ch in _TOP_LEFT:
                tr = None
                for cc in range(c + 2, width):
                    if row[cc] in _TOP_RIGHT and all(
                        row[k] in _H_EDGE or row[k] in _TOP_LEFT or row[k] in _TOP_RIGHT
                        for k in range(c + 1, cc)
                    ):
                        tr = cc
                        break
                if tr is None:
                    continue
                br = None
                for rr in range(r + 1, height):
                    left, right = padded[rr][c], padded[rr][tr]
                    if left in _BOT_LEFT and right in _BOT_RIGHT:
                        br = rr
                        break
                    if left not in _V_EDGE and left not in _TOP_LEFT:
                        break
                if br is None:
                    continue
                take(r, br, c, tr, "unicode")

    ascii_edge = re.compile(r"[+][-=]{2,}[+]")
    for r, row in enumerate(padded):
        for match in ascii_edge.finditer(row):
            c0, c1 = match.start(), match.end() - 1
            if used[r][c0] or used[r][c1]:
                continue
            br = None
            for rr in range(r + 1, height):
                if c1 >= len(padded[rr]):
                    continue
                left, right = padded[rr][c0], padded[rr][c1]
                if left == "+" and right == "+" and re.match(r"[+][-=]{2,}[+]", padded[rr][c0 : c1 + 1]):
                    br = rr
                    break
                if left not in "|+" or right not in "|+":
                    break
            if br is None:
                continue
            take(r, br, c0, c1, "ascii")

    boxes.sort(key=lambda b: (b.r0, b.c0))
    return boxes


def _cluster_bands(boxes: Sequence[_Box]) -> List[List[_Box]]:
    """Group boxes that overlap vertically (a left-to-right row of components)."""
    if not boxes:
        return []
    ordered = sorted(boxes, key=lambda b: (b.r0, b.c0))
    bands: List[List[_Box]] = []
    current = [ordered[0]]
    band_r1 = ordered[0].r1
    for box in ordered[1:]:
        if box.r0 <= band_r1 + 1:
            current.append(box)
            band_r1 = max(band_r1, box.r1)
        else:
            bands.append(current)
            current = [box]
            band_r1 = box.r1
    bands.append(current)
    for band in bands:
        band.sort(key=lambda b: b.c0)
    return bands


def compose_box_row(snippets: Sequence[Sequence[str]], arrow: str) -> List[str]:
    blocks = [list(s) for s in snippets if s]
    if not blocks:
        return []
    if len(blocks) == 1:
        return list(blocks[0])
    heights = [len(b) for b in blocks]
    height = max(heights)
    padded: List[List[str]] = []
    for block in blocks:
        w = max((len(ln) for ln in block), default=0)
        aligned = [ln.ljust(w) for ln in block]
        top = (height - len(aligned)) // 2
        bot = height - len(aligned) - top
        padded.append([" " * w] * top + aligned + [" " * w] * bot)
    gap = " " * len(arrow)
    arrow_row = height // 2
    lines: List[str] = []
    for r in range(height):
        parts: List[str] = []
        for i, block in enumerate(padded):
            if i:
                parts.append(arrow if r == arrow_row else gap)
            parts.append(block[r])
        lines.append("".join(parts).rstrip())
    return lines


def _vertical_joiner(width: int) -> List[str]:
    mid = max(0, width // 2)
    return ["", (" " * mid) + "│", (" " * mid) + "v", ""]


def pack_boxes_to_width(boxes: Sequence[_Box], max_cols: int) -> List[str]:
    """Flex-wrap boxes into rows that fit max_cols, stacked top-down."""
    if not boxes:
        return []
    prepared: List[Tuple[_Box, List[str]]] = []
    for box in boxes:
        prepared.append((box, shrink_box_snippet(box.snippet, max_cols, box.style)))

    arrow = _H_ARROW if any(b.style == "unicode" for b in boxes) else _ASCII_H_ARROW
    gap = len(arrow)

    rows: List[List[List[str]]] = []
    current: List[List[str]] = []
    current_w = 0
    for _, snippet in prepared:
        w = max((len(ln) for ln in snippet), default=0)
        extra = 0 if not current else gap
        if current and current_w + extra + w > max_cols:
            rows.append(current)
            current = [snippet]
            current_w = w
        else:
            current.append(snippet)
            current_w += extra + w
    if current:
        rows.append(current)

    rendered_rows = [compose_box_row(row, arrow) for row in rows]
    out: List[str] = []
    for i, row_lines in enumerate(rendered_rows):
        if i:
            width = max((len(ln) for ln in row_lines), default=8)
            out.extend(_vertical_joiner(min(width, max_cols)))
        out.extend(row_lines)
    return out


def reflow_boxes(lines: Sequence[str], max_cols: int) -> Optional[List[str]]:
    boxes = extract_boxes(lines)
    if len(boxes) < 1:
        return None
    width = max((len(_expand(ln)) for ln in lines), default=0)
    if width <= max_cols and all(box.width <= max_cols for box in boxes):
        return None  # caller keeps original
    bands = _cluster_bands(boxes)
    fitted: List[str] = []
    for band in bands:
        packed = pack_boxes_to_width(band, max_cols)
        if not packed:
            return None
        if fitted:
            width = max((len(ln) for ln in packed), default=8)
            fitted.extend(_vertical_joiner(min(width, max_cols)))
        fitted.extend(packed)
    if not fitted or any(len(ln) > max_cols for ln in fitted):
        return None
    return fitted


def _split_fence(lines: Sequence[str]) -> Optional[Tuple[str, List[str], str]]:
    if len(lines) < 3:
        return None
    if _FENCE_RE.match(_expand(lines[0]).strip()) and _FENCE_RE.match(_expand(lines[-1]).strip()):
        return _expand(lines[0]).strip(), list(lines[1:-1]), _expand(lines[-1]).strip()
    return None


def fit_diagram(lines: Sequence[str], max_cols: int) -> List[str]:
    """Return diagram lines that each fit in max_cols without wrapping."""
    budget = max(MIN_COLS, int(max_cols))
    expanded = [_expand(ln) for ln in lines]
    fenced = _split_fence(expanded)
    if fenced:
        head, body, tail = fenced
        return [head, *fit_diagram(body, budget), tail]

    dedented = _dedent(expanded)
    width = max((len(ln) for ln in dedented), default=0)
    if width <= budget:
        return dedented

    boxed = reflow_boxes(dedented, budget)
    if boxed is not None:
        return boxed

    panels = split_into_column_panels(dedented, budget)
    safe: List[List[str]] = []
    for panel in panels:
        pw = max((len(ln) for ln in panel), default=0)
        if pw <= budget:
            safe.append(list(panel))
        else:
            safe.extend(wrap_as_grid(panel, budget))
    fitted = stack_panels(safe)
    # Final guard: never emit a line wider than the window.
    guarded: List[str] = []
    for ln in fitted:
        if len(ln) <= budget:
            guarded.append(ln)
        else:
            for i in range(0, len(ln), budget):
                guarded.append(ln[i : i + budget])
    return guarded


def layout_diagrams_in_text(text: str, max_cols: int) -> str:
    """Reflow every detected diagram block in `text` to max_cols."""
    if not text:
        return text
    lines = text.split("\n")
    blocks = find_diagram_blocks(lines)
    if not blocks:
        return text
    budget = max(MIN_COLS, int(max_cols))
    for start, end in reversed(blocks):
        original = lines[start : end + 1]
        lines[start : end + 1] = fit_diagram(original, budget)
    return "\n".join(lines)


def diagram_block_line_ranges(text: str) -> List[BoxRange]:
    """Line ranges after layout (for UI tagging)."""
    return find_diagram_blocks(text.split("\n"))


def max_line_width(text: str) -> int:
    if not text:
        return 0
    return max((len(_expand(ln)) for ln in text.split("\n")), default=0)


class DiagramBuffer:
    """
    Keep the unfitted document so resize can reflow without compounding splits.

    Widget shows the laid-out copy. New Q&A is appended after the laid-out text;
    `apply()` maps that suffix back onto the original source.
    """

    def __init__(self) -> None:
        self.source: Optional[str] = None
        self.displayed: Optional[str] = None
        self.applied_cols: Optional[int] = None

    def reset(self) -> None:
        self.source = None
        self.displayed = None
        self.applied_cols = None

    def set_unfitted_source(self, text: str) -> None:
        self.source = text
        self.displayed = None
        self.applied_cols = None

    def apply(self, widget_text: str, max_cols: int) -> str:
        budget = max(MIN_COLS, int(max_cols))
        if self.source is None or self.displayed is None:
            self.source = widget_text
        elif widget_text == self.displayed:
            pass
        elif self.displayed and widget_text.startswith(self.displayed):
            suffix = widget_text[len(self.displayed) :]
            if suffix:
                self.source = self.source + suffix
        else:
            self.source = widget_text

        laid = layout_diagrams_in_text(self.source or "", budget)
        self.displayed = laid
        self.applied_cols = budget
        return laid
