"""ASCII / system-design flowchart layout — fits any column width."""

from __future__ import annotations

import textwrap

import pytest

from ascii_diagram import (
    CONTINUATION_LINES,
    DiagramBuffer,
    estimate_char_columns,
    extract_boxes,
    find_diagram_blocks,
    fit_diagram,
    is_diagram_line,
    layout_diagrams_in_text,
    max_line_width,
    pack_boxes_to_width,
    shrink_box_snippet,
)


WIDE_FLOWCHART = textwrap.dedent(
    """
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │    Client    │────▶│  API Gateway │────▶│  User Service│────▶│   Database   │
    └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
    """
).strip("\n")

ASCII_FLOWCHART = textwrap.dedent(
    """
        +-----------+         +-----------+         +-----------+
        |   User    |-------->|   Auth    |-------->|   Redis   |
        +-----------+         +-----------+         +-----------+
    """
).strip("\n")

PROSE = textwrap.dedent(
    """
    A load balancer sits in front of the API. Use a cache | queue | DB
    depending on the access pattern. The flow is request -> service then store.
    """
).strip()


def _assert_fits(text: str, cols: int) -> None:
    for i, line in enumerate(text.split("\n")):
        assert len(line) <= cols, f"line {i} width {len(line)} > {cols}: {line!r}"


def test_box_drawing_lines_are_diagrams():
    for line in WIDE_FLOWCHART.split("\n"):
        assert is_diagram_line(line), line


def test_ascii_plus_box_lines_are_diagrams():
    for line in ASCII_FLOWCHART.split("\n"):
        assert is_diagram_line(line), line


def test_prose_is_not_a_diagram():
    for line in PROSE.split("\n"):
        assert not is_diagram_line(line), line


def test_ui_separators_are_not_diagrams():
    assert not is_diagram_line("---------------------------------------------------------------------")
    assert not is_diagram_line("------------------")
    assert not is_diagram_line("QUESTION: design a URL shortener")
    assert not is_diagram_line("ANSWER: here is the design")
    assert not is_diagram_line("Live Question: tell me about Kafka")


def test_finds_flowchart_block_inside_prose():
    text = "Intro text.\n\n" + WIDE_FLOWCHART + "\n\nClosing remarks."
    blocks = find_diagram_blocks(text.split("\n"))
    assert len(blocks) == 1
    start, end = blocks[0]
    body = "\n".join(text.split("\n")[start : end + 1])
    assert "Client" in body and "Database" in body
    assert "Intro text" not in body
    assert "Closing" not in body


def test_fenced_diagram_is_one_block():
    text = textwrap.dedent(
        """
        Design:

        ```
        ┌─────┐     ┌─────┐
        │  A  │────▶│  B  │
        └─────┘     └─────┘
        ```

        Notes follow.
        """
    ).strip()
    blocks = find_diagram_blocks(text.split("\n"))
    assert len(blocks) == 1
    start, end = blocks[0]
    chunk = text.split("\n")[start : end + 1]
    assert chunk[0].strip().startswith("```")
    assert chunk[-1].strip().startswith("```")


def test_wide_flowchart_fits_narrow_window():
    for cols in (24, 32, 40, 48, 56, 72, 80, 120):
        fitted = layout_diagrams_in_text(WIDE_FLOWCHART, cols)
        _assert_fits(fitted, cols)
        assert "Client" in fitted
        assert "Database" in fitted
        assert "API Gateway" in fitted
        assert "User Service" in fitted


def test_ascii_flowchart_fits_narrow_window():
    for cols in (24, 36, 48, 80):
        fitted = layout_diagrams_in_text(ASCII_FLOWCHART, cols)
        _assert_fits(fitted, cols)
        assert "User" in fitted
        assert "Auth" in fitted
        assert "Redis" in fitted


def test_narrow_diagram_unchanged_alignment():
    narrow = textwrap.dedent(
        """
        ┌─────────┐
        │  Cache  │
        └────┬────┘
             │
             v
        ┌─────────┐
        │   DB    │
        └─────────┘
        """
    ).strip("\n")
    fitted = layout_diagrams_in_text(narrow, 80)
    # Relative box alignment must survive (no wrap artifacts).
    lines = [ln for ln in fitted.split("\n") if ln.strip()]
    tops = [ln for ln in lines if ln.strip().startswith("┌")]
    assert len(tops) == 2
    assert tops[0].index("┌") == tops[1].index("┌")


def test_wide_flowchart_stacks_instead_of_wrapping_spaces():
    fitted = layout_diagrams_in_text(WIDE_FLOWCHART, 36)
    _assert_fits(fitted, 36)
    # A wrap=WORD break would put "│    Client    │" fragments on their own
    # lines without matching box corners. After fit, every side line still
    # has both left and right box edges.
    for ln in fitted.split("\n"):
        if "│" in ln and any(name in ln for name in ("Client", "API Gateway", "User Service", "Database")):
            assert ln.strip().startswith("│")
            assert ln.strip().endswith("│")
    # Left-to-right chain becomes stacked sections.
    assert any(ln.strip() in {"│", "|"} for ln in fitted.split("\n"))
    assert any(ln.strip() == "v" for ln in fitted.split("\n"))


def test_boxes_are_extracted_intact_and_packed():
    boxes = extract_boxes(WIDE_FLOWCHART.split("\n"))
    assert len(boxes) == 4
    labels = " ".join(_inner for _inner in (_box_label(b) for b in boxes))
    assert "Client" in labels
    assert "Database" in labels
    packed = pack_boxes_to_width(boxes, 40)
    _assert_fits("\n".join(packed), 40)
    for ln in packed:
        if any(name in ln for name in ("Client", "API Gateway", "User Service", "Database")):
            assert ln.strip().startswith("│")
            assert ln.strip().endswith("│")


def _box_label(box) -> str:
    return " ".join(ln.strip("│| ") for ln in box.snippet[1:-1])


def test_prose_around_diagram_is_preserved():
    text = "Before the design.\n\n" + WIDE_FLOWCHART + "\n\nAfter the design."
    laid = layout_diagrams_in_text(text, 40)
    assert laid.startswith("Before the design.")
    assert laid.rstrip().endswith("After the design.")
    _assert_fits("\n".join(laid.split("\n")[2:-2]), 40)


def test_tree_diagram_detected_and_fits():
    tree = textwrap.dedent(
        """
            API
            |
            +-- /users
            |     +-- GET
            |     +-- POST
            +-- /orders
                  +-- GET
        """
    ).strip("\n")
    blocks = find_diagram_blocks(tree.split("\n"))
    assert blocks
    laid = layout_diagrams_in_text(tree, 24)
    _assert_fits(laid, 24)
    assert "/users" in laid
    assert "/orders" in laid


def test_single_arrow_flow_line_fits():
    line = "Client --> API Gateway --> Worker --> Queue --> Database"
    laid = layout_diagrams_in_text(line, 28)
    _assert_fits(laid, 28)
    assert "Client" in laid
    assert "Database" in laid


def test_estimate_char_columns_scales_with_width_and_font():
    wide = estimate_char_columns(800, 12)
    narrow = estimate_char_columns(320, 12)
    big_font = estimate_char_columns(800, 20)
    assert wide > narrow
    assert wide > big_font
    assert narrow >= 16


def test_diagram_buffer_resize_does_not_compound():
    buf = DiagramBuffer()
    first = buf.apply(WIDE_FLOWCHART, 80)
    assert max_line_width(first) <= 80
    # Resize narrower using the already-displayed widget text.
    second = buf.apply(first, 32)
    _assert_fits(second, 32)
    assert "Client" in second and "Database" in second
    # Resize back wide — should recover a left-to-right (or still stacked but complete) view from SOURCE.
    third = buf.apply(second, 120)
    _assert_fits(third, 120)
    # Source must still be the original wide chart, not a stacked-then-restacked mess.
    assert buf.source == WIDE_FLOWCHART
    assert third.count("Client") == 1
    assert third.count("Database") == 1


def test_diagram_buffer_appends_new_answer_suffix():
    buf = DiagramBuffer()
    laid = buf.apply("Intro\n" + WIDE_FLOWCHART, 80)
    extra = "\n\nQUESTION: scale it\nANSWER:\n" + ASCII_FLOWCHART
    combined_widget = laid + extra
    updated = buf.apply(combined_widget, 36)
    _assert_fits(updated, 36)
    assert "Client" in updated
    assert "Redis" in updated
    assert "QUESTION: scale it" in updated


def test_diagram_buffer_rebuild_replaces_source():
    buf = DiagramBuffer()
    buf.apply(WIDE_FLOWCHART, 80)
    rebuilt = "New chat\n" + ASCII_FLOWCHART
    laid = buf.apply(rebuilt, 40)
    assert "Redis" in laid
    assert "Client" not in laid
    _assert_fits(laid, 40)


def test_fit_never_emits_continuation_wider_than_budget():
    for line in CONTINUATION_LINES:
        assert len(line) <= 16


def test_already_fitting_text_is_stable():
    src = "Hello world.\nThis is a short answer."
    assert layout_diagrams_in_text(src, 40) == src


def test_word_wrap_regression_spaces_inside_boxes():
    """
    wrap=WORD would break '│    Client    │' at the spaces and destroy the box.
    After fitting to a width smaller than the original row, each remaining box
    row must stay a single intact line.
    """
    original_width = max_line_width(WIDE_FLOWCHART)
    assert original_width > 40
    fitted = fit_diagram(WIDE_FLOWCHART.split("\n"), 40)
    for ln in fitted:
        assert len(ln) <= 40
        if "Client" in ln:
            assert "│" in ln and ln.count("│") >= 2
            # Not split into '│    ' and 'Client    │'
            assert "Client" in ln
            assert ln.strip()[0] in "│|"
            assert ln.strip()[-1] in "│|"


def test_two_by_two_grid_keeps_row_bands():
    grid = textwrap.dedent(
        """
        ┌─────────┐     ┌─────────┐
        │   Web   │────▶│   API   │
        └─────────┘     └─────────┘
               │               │
               v               v
        ┌─────────┐     ┌─────────┐
        │  Cache  │     │   DB    │
        └─────────┘     └─────────┘
        """
    ).strip("\n")
    boxes = extract_boxes(grid.split("\n"))
    assert len(boxes) == 4
    fitted = layout_diagrams_in_text(grid, 28)
    _assert_fits(fitted, 28)
    for name in ("Web", "API", "Cache", "DB"):
        assert name in fitted


def test_oversized_single_box_shrinks_and_wraps_label():
    wide_box = textwrap.dedent(
        """
        ┌──────────────────────────────────────────────┐
        │ User Authentication and Session Management   │
        └──────────────────────────────────────────────┘
        """
    ).strip("\n")
    assert max_line_width(wide_box) > 32
    fitted = layout_diagrams_in_text(wide_box, 28)
    _assert_fits(fitted, 28)
    assert "Authentication" in fitted
    assert fitted.strip().startswith("┌")
    assert fitted.strip().endswith("┘")
    boxes = extract_boxes(wide_box.split("\n"))
    shrunk = shrink_box_snippet(boxes[0].snippet, 28, "unicode")
    _assert_fits("\n".join(shrunk), 28)
    assert any("Auth" in ln for ln in shrunk)


def test_tk_text_widget_reflow_fits_window():
    tk = pytest.importorskip("tkinter")
    from ascii_diagram import DiagramBuffer as _Buf

    root = tk.Tk()
    root.withdraw()
    try:
        text = tk.Text(root, wrap=tk.WORD, font=("Courier", 12), width=40, height=20)
        text.pack()
        root.update_idletasks()
        char_w = 7
        try:
            from tkinter import font as tkfont
            char_w = max(1, tkfont.Font(font=text.cget("font")).measure("0"))
        except Exception:
            pass
        cols = max(16, (int(text.winfo_reqwidth()) - 10) // char_w)
        text.insert("1.0", "ANSWER:\n" + WIDE_FLOWCHART)
        buf = _Buf()
        laid = buf.apply(text.get("1.0", "end-1c"), cols)
        text.delete("1.0", tk.END)
        text.insert("1.0", laid)
        stored = text.get("1.0", "end-1c")
        _assert_fits(stored, cols)
        assert "Client" in stored and "Database" in stored
        for ln in stored.split("\n"):
            if "Client" in ln:
                assert ln.strip().startswith("│")
                assert ln.strip().endswith("│")
    finally:
        root.destroy()

