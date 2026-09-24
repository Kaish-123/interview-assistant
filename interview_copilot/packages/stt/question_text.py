"""Assemble a full interview question from paused / fragmented speech."""

from __future__ import annotations

import re

_TRAILING_INCOMPLETE = re.compile(
    r"(?:,|:|;|-|—|/|\band\b|\bor\b|\bbut\b|\bthe\b|\ba\b|\ban\b|\bto\b|\bof\b|"
    r"\bfor\b|\bwith\b|\bthat\b|\bwhich\b|\bwho\b|\bhow\b|\bwhat\b|\bwhen\b|"
    r"\bwhy\b|\bcan\b|\bcould\b|\bwould\b|\bshould\b|\bis\b|\bare\b|\bwas\b|"
    r"\byour\b|\bmy\b|\bin\b|\bon\b)\s*$",
    re.IGNORECASE,
)

_END_PUNCT = re.compile(r"[.?!][\"')\]]*\s*$")
_QUESTION_MARK = re.compile(r"\?\s*$")

# Human pauses inside a question vs a real handoff to the candidate.
SHORT_PAUSE_MS = 900
MERGE_WINDOW_MS = 3200
ANSWER_SILENCE_MS = 1500
INCOMPLETE_SILENCE_MS = 2200

_TRAILING_CONTINUE = re.compile(
    r"(?:\blike\b|\bsuch as\b|\bfor example\b|\bspecifically\b|\bincluding\b|"
    r"\bbasically\b|\bmaybe\b|\bperhaps\b|\bso\b|\bthen\b|\balso\b|\bplus\b|"
    r"\bwhich\b|\bwhere\b)\s*$",
    re.IGNORECASE,
)


def word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w])


def looks_like_question(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 8:
        return False
    lower = t.lower()
    markers = (
        "?", "tell me", "describe", "explain", "how do", "how does", "how would",
        "what is", "what are", "what would", "walk me", "walk through", "can you",
        "could you", "would you", "why did", "why do", "design a", "implement",
    )
    if any(m in lower for m in markers):
        return True
    return word_count(t) >= 12


def is_incomplete_question(text: str) -> bool:
    """True while the interviewer is still mid-clause — not a cue to answer yet."""
    t = (text or "").strip()
    if not t:
        return True
    if _TRAILING_INCOMPLETE.search(t) or _TRAILING_CONTINUE.search(t):
        return True
    wc = word_count(t)
    if _QUESTION_MARK.search(t) and wc >= 4:
        return False
    if _END_PUNCT.search(t):
        return wc < 8
    # Unpunctuated STT of a short stem is usually the start of a longer question.
    return wc < 16


def answer_hold_ms(text: str) -> int:
    """How long the interviewer must stay quiet before we call the LLM."""
    if is_incomplete_question(text):
        return INCOMPLETE_SILENCE_MS
    if _QUESTION_MARK.search((text or "").strip()) and word_count(text) >= 5:
        return 1200
    return ANSWER_SILENCE_MS


def question_ready_to_answer(
    text: str,
    quiet_ms: int,
    *,
    speaking: bool = False,
) -> bool:
    """Answer only after a real pause, once this sounds like a finished question."""
    if speaking:
        return False
    t = (text or "").strip()
    if not t:
        return False
    if quiet_ms < answer_hold_ms(t):
        return False
    if looks_like_question(t):
        return True
    return word_count(t) >= 12


_WORD_KEY = re.compile(r"[^a-z0-9']+")


def _word_key(w: str) -> str:
    return _WORD_KEY.sub("", (w or "").lower())


def _token_keys(text: str) -> list[str]:
    return [k for w in (text or "").split() if (k := _word_key(w))]


def collapse_revision_loops(text: str) -> str:
    """Drop earlier STT revisions that restart a 5+ word phrase already said."""
    words = [w for w in (text or "").split() if w]
    for _ in range(24):
        n = len(words)
        if n < 16:
            break
        removed = False
        for width in range(min(14, n // 2), 4, -1):
            first: dict[tuple[str, ...], int] = {}
            for i in range(0, n - width + 1):
                key = tuple(_word_key(x) for x in words[i : i + width])
                if not all(key):
                    continue
                if key in first:
                    j = first[key]
                    if i - j < width:
                        continue
                    words = words[:j] + words[i:]
                    removed = True
                    break
                first[key] = i
            if removed:
                break
        if not removed:
            break
    return " ".join(words)


def max_shared_ngram(a: str, b: str, min_n: int = 5) -> int:
    """Longest run of tokens that appears in both strings."""
    ka, kb = _token_keys(a), _token_keys(b)
    if len(ka) < min_n or len(kb) < min_n:
        return 0
    top = min(14, len(ka), len(kb))
    for width in range(top, min_n - 1, -1):
        other = {tuple(kb[i : i + width]) for i in range(len(kb) - width + 1)}
        for i in range(len(ka) - width + 1):
            if tuple(ka[i : i + width]) in other:
                return width
    return 0


def collapse_repeated_phrase(text: str) -> str:
    """If STT printed the same question twice, keep one copy."""
    words = [w for w in (text or "").split() if w]
    n = len(words)
    if n < 4:
        return " ".join(words)
    mid = n // 2
    if words[:mid] == words[mid : mid * 2] and n - mid * 2 <= 1:
        return " ".join(words[:mid])
    for size in range(2, mid + 1):
        if n < size * 2:
            break
        chunk = words[:size]
        if words[: size * 2] == chunk + chunk:
            return " ".join(chunk + words[size * 2 :])
    return " ".join(words)


def collapse_snowball(text: str) -> str:
    """Undo STT that appended every growing hypothesis onto the last one."""
    t = collapse_repeated_phrase(" ".join((text or "").split()))
    if not t:
        return t
    t = collapse_revision_loops(t)
    prev = None
    while prev != t:
        prev = t
        words = t.split()
        if len(words) < 14:
            break
        stem_n = 6 if len(words) >= 12 else 4
        stem = " ".join(words[:stem_n]).lower()
        lower = t.lower()
        last = lower.rfind(stem)
        if last > 8:
            t = t[last:].strip()
            t = collapse_repeated_phrase(t)
            t = collapse_revision_loops(t)
        else:
            break
    return collapse_revision_loops(t)


def _stem_len(a: str, b: str) -> int:
    wa = a.lower().split()
    wb = b.lower().split()
    n = 0
    for x, y in zip(wa, wb):
        if x != y:
            break
        n += 1
    return n


def coalesce_transcript(prev: str, nxt: str) -> str:
    """Combine two STT sources. Growing captions replace; never snowball-append."""
    a = collapse_snowball(prev or "")
    b = collapse_snowball(nxt or "")
    if not a:
        return b
    if not b:
        return a
    al, bl = a.lower(), b.lower()
    if al == bl:
        return b if len(b) >= len(a) else a
    shared = max_shared_ngram(a, b)
    if _stem_len(a, b) >= 5:
        return b if word_count(b) >= word_count(a) else a
    if shared >= 5:
        wa, wb = word_count(a), word_count(b)
        if wa > wb * 1.5 and wb >= 6:
            return b
        return b if wb >= wa else a
    if bl in al:
        return a
    if al in bl:
        return b
    return collapse_snowball(merge_fragments(a, b))


def collapse_caption_results(parts: list[str] | tuple[str, ...]) -> str:
    """Fold SpeechRecognition results. Growing hypotheses replace; new clauses merge."""
    out = ""
    for part in parts or ():
        piece = " ".join((part or "").split())
        if not piece:
            continue
        out = coalesce_transcript(out, piece)
    return collapse_snowball(out)


def merge_fragments(prev: str, nxt: str) -> str:
    a = (prev or "").strip()
    b = (nxt or "").strip()
    if not a:
        return b
    if not b:
        return a
    if b.lower() in a.lower():
        return a
    if a.lower() in b.lower() and len(b) > len(a):
        return b
    if a.endswith("-") or a.endswith("—"):
        return a.rstrip("-— ") + b
    gap = "" if a.endswith((" ", "\n")) else " "
    return f"{a}{gap}{b}"


def should_merge_fragments(prev: str, nxt: str, gap_ms: int) -> bool:
    if not (prev or "").strip() or not (nxt or "").strip():
        return False
    if gap_ms > MERGE_WINDOW_MS:
        return False
    if is_incomplete_question(prev):
        return True
    if gap_ms <= SHORT_PAUSE_MS:
        return True
    if nxt[:1].islower():
        return True
    return False


def next_word_chunk(shown: str, want: str) -> str | None:
    """Next word (plus its trailing space) so `shown` types toward `want`."""
    shown = shown or ""
    want = want or ""
    if not want or shown == want:
        return None
    if not shown:
        m = re.match(r"\S+\s*", want)
        return m.group(0) if m else want
    if want.startswith(shown):
        rest = want[len(shown) :]
        m = re.match(r"\s*\S+\s*", rest)
        return m.group(0) if m else rest
    m = re.match(r"\S+\s*", want)
    return m.group(0) if m else want


def question_type_chunks(suffix: str) -> list[str]:
    """Split a burst of new question text into word-sized inserts."""
    if not suffix:
        return []
    if "\n" in suffix or "ANSWER:" in suffix:
        return [suffix]
    parts = suffix.split(" ")
    out: list[str] = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            out.append(f"{part} ")
        elif part:
            out.append(part)
    return [c for c in out if c]


def is_close_enough_for_prefetch(partial: str, full: str) -> bool:
    a = (partial or "").strip().lower()
    b = (full or "").strip().lower()
    if not a or not b:
        return False
    if b.startswith(a) and len(b) - len(a) <= 80:
        return True
    if a.startswith(b):
        return True
    n = min(len(a), len(b), 48)
    return n >= 24 and a[:n] == b[:n]
