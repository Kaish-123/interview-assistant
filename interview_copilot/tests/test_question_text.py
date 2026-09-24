"""Tests for assembling paused interview questions."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from interview_copilot.packages.stt.question_text import (
    collapse_caption_results,
    collapse_repeated_phrase,
    collapse_snowball,
    coalesce_transcript,
    is_close_enough_for_prefetch,
    is_incomplete_question,
    merge_fragments,
    next_word_chunk,
    question_type_chunks,
    should_merge_fragments,
)

ROOT = Path(__file__).resolve().parents[1]
QUESTION_JS = ROOT / "apps/web/static/js/question.js"

# Growing SpeechRecognition hypotheses from the live-captions snowball screenshot.
_STEM = (
    "If you want to talk to computer you need to you need to talk to them in terms of"
)
_GROWING_TAILS = (
    "want to talk to come.",
    "zer",
    "zeros",
    "zeros and",
    "zeros and ones",
    "zeros and ones now",
    "zeros and ones now it",
    "zeros and ones now it is",
    "zeros and ones now it is not",
    "zeros and ones now it is not technically",
    "zeros and ones now it is not technically possible",
    "zeros and ones now it is not technically possible right",
    "zeros and ones now it is not technically possible right of course",
)


def _hypotheses() -> list[str]:
    return [f"{_STEM} {tail}" for tail in _GROWING_TAILS]


def _snowball_blob() -> str:
    return " ".join(_hypotheses())


def test_incomplete_trailing_and():
    assert is_incomplete_question("Tell me about a time you led a project and")
    assert is_incomplete_question("How would you design a URL shortener")
    assert is_incomplete_question("How would you design a")
    assert not is_incomplete_question("Tell me about yourself?")
    assert not is_incomplete_question(
        "How would you design a URL shortener for a billion users?"
    )
    assert not is_incomplete_question(
        "Tell me about a time you disagreed with a teammate on a technical choice and how you resolved it."
    )


def test_waits_for_pause_before_answering():
    from interview_copilot.packages.stt.question_text import (
        answer_hold_ms,
        question_ready_to_answer,
    )

    mid = "How would you design a URL shortener"
    done = "How would you design a URL shortener for a billion users?"
    assert answer_hold_ms(mid) >= 2000
    assert not question_ready_to_answer(done, 400)
    assert not question_ready_to_answer(done, 5000, speaking=True)
    assert question_ready_to_answer(done, 1600)
    # Keep assembling through a thinking pause inside one question.
    prev = "Can you walk me through a system you designed"
    nxt = "that handled millions of events per day?"
    assert should_merge_fragments(prev, nxt, 2000)


def test_merge_short_pause_keeps_full_question():
    prev = "Can you walk me through a system you designed"
    nxt = "that handled millions of events per day?"
    assert should_merge_fragments(prev, nxt, 900)
    assert "millions of events" in merge_fragments(prev, nxt)


def test_does_not_merge_after_long_gap_when_complete():
    prev = "Tell me about yourself?"
    nxt = "What is your notice period?"
    assert not should_merge_fragments(prev, nxt, 6000)


def test_js_question_helper_matches_python_rules():
    js = QUESTION_JS.read_text(encoding="utf-8")
    assert "shouldMergeFragments" in js
    assert "isIncompleteQuestion" in js
    assert "MERGE_WINDOW_MS = 3200" in js
    assert "SHORT_PAUSE_MS = 900" in js
    assert "ANSWER_SILENCE_MS = 1500" in js
    assert "questionReadyToAnswer" in js
    assert "answerHoldMs" in js
    assert "coalesceTranscript" in js
    assert "collapseSnowball" in js
    assert "collapseCaptionResults" in js
    assert "collapseRevisionLoops" in js
    assert "nextWordChunk" in js
    assert "questionTypeChunks" in js


def test_prefetch_prefix():
    partial = "how would you design a url shortener"
    full = "how would you design a url shortener for a billion users?"
    assert is_close_enough_for_prefetch(partial, full)
    assert not is_close_enough_for_prefetch("hello there colleague", "design a cache")
    doubled = "what is python what is python"
    assert collapse_repeated_phrase(doubled) == "what is python"
    assert coalesce_transcript("what is python", "what is python used for") == "what is python used for"
    assert coalesce_transcript("what is python used for", "what is python") == "what is python used for"


def test_collapse_snowball_undoes_growing_hypothesis_concat():
    blob = _snowball_blob()
    assert blob.count("If you want to talk to") == len(_GROWING_TAILS)
    cleaned = collapse_snowball(blob)
    assert cleaned == _hypotheses()[-1]
    assert cleaned.count("If you want to talk to") == 1
    assert cleaned.endswith("of course")
    assert "come." not in cleaned


def test_coalesce_growing_captions_replaces_never_appends():
    acc = ""
    for piece in _hypotheses():
        acc = coalesce_transcript(acc, piece)
    assert acc == _hypotheses()[-1]
    short = _hypotheses()[2]
    long = _hypotheses()[-1]
    assert coalesce_transcript(short, long) == long
    assert coalesce_transcript(long, short) == long
    # Divergent tails that share a stem must not concatenate.
    a = f"{_STEM} come."
    b = f"{_STEM} zeros"
    merged = coalesce_transcript(a, b)
    assert merged.count("If you want to talk to") == 1
    assert "come." not in merged
    assert merged.endswith("zeros")


def test_collapse_caption_results_folds_chrome_finals():
    parts = _hypotheses()
    assert collapse_caption_results(parts) == parts[-1]
    # Genuine new clause after a different opening still concatenates.
    combined = collapse_caption_results(
        ["How does TCP work?", "And what is UDP used for?"]
    )
    assert "TCP" in combined and "UDP" in combined


def test_js_collapse_snowball_matches_python():
    blob = _snowball_blob()
    last = _hypotheses()[-1]
    script = r"""
const fs = require("fs");
const vm = require("vm");
const ctx = { window: {}, console };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const Q = ctx.window.QuestionText;
const blob = process.argv[2];
const last = process.argv[3];
const parts = JSON.parse(process.argv[4]);
const cleaned = Q.collapseSnowball(blob);
if (cleaned !== last) {
  console.error("snowball", cleaned);
  process.exit(1);
}
let acc = "";
for (const p of parts) acc = Q.coalesceTranscript(acc, p);
if (acc !== last) {
  console.error("coalesce", acc);
  process.exit(1);
}
const folded = Q.collapseCaptionResults(parts);
if (folded !== last) {
  console.error("caption", folded);
  process.exit(1);
}
console.log("ok");
"""
    proc = subprocess.run(
        [
            "node",
            "-e",
            script,
            str(QUESTION_JS),
            blob,
            last,
            json.dumps(_hypotheses()),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "ok" in proc.stdout


LOOPY_CAPTION = (
    "We have some a grammatical stuff here so what we have done is we Have created "
    "programming languages now those are not actually stuff here. So, what we have done "
    "is we have grammatical stuff here. So what we have done is we have created programming "
    "languages now those are not actually stuff here. So, what we have done is we have "
    "created programming languages. Now, those are not actually grammatical stuff here. "
    "So what we have done is we have created programming languages. Now, those are not actually."
)


def test_collapse_revision_loops_in_one_utterance():
    cleaned = collapse_snowball(LOOPY_CAPTION)
    assert cleaned.lower().count("what we have done is") == 1
    assert cleaned.lower().count("created programming languages") == 1
    assert len(cleaned.split()) < 40
    caption = (
        "We have some a grammatical stuff here so what we have done is we Have created "
        "programming languages now those are not actually"
    )
    whisper = (
        "stuff here. So, what we have done is we have created programming languages. "
        "Now, those are not actually."
    )
    merged = coalesce_transcript(caption, whisper)
    assert merged.lower().count("what we have done is") == 1
    assert merged.lower().count("created programming languages") == 1
    # Caption then Whisper finalize must not stack the same question twice.
    stacked = coalesce_transcript(cleaned, cleaned)
    assert stacked.lower().count("what we have done is") == 1


def test_js_revision_loop_matches_python():
    py = collapse_snowball(LOOPY_CAPTION)
    script = r"""
const fs = require("fs");
const vm = require("vm");
const ctx = { window: {}, console };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const got = ctx.window.QuestionText.collapseSnowball(process.argv[2]);
const want = process.argv[3];
if (got !== want) {
  console.error("js", got);
  console.error("py", want);
  process.exit(1);
}
const idle = "Waiting for the interviewer…";
const liveLeft = got;
const committedLeft = idle;
if (liveLeft === committedLeft) process.exit(2);
if (committedLeft.includes("programming languages")) process.exit(3);
if (!got.toLowerCase().includes("programming languages")) process.exit(4);
console.log("ok");
"""
    proc = subprocess.run(
        ["node", "-e", script, str(QUESTION_JS), LOOPY_CAPTION, py],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "ok" in proc.stdout


def test_next_word_chunk_types_toward_target():
    want = "How would you design a URL shortener?"
    shown = ""
    steps = []
    while True:
        chunk = next_word_chunk(shown, want)
        if not chunk:
            break
        shown += chunk
        steps.append(chunk)
        if len(steps) > 40:
            break
    assert shown == want
    assert len(steps) == len(want.split())
    assert steps[0].startswith("How")
    assert next_word_chunk(want, want) is None
    assert question_type_chunks("hello there world") == ["hello ", "there ", "world"]
    assert question_type_chunks("hello\nANSWER: no") == ["hello\nANSWER: no"]


def test_js_next_word_chunk_matches_python():
    want = "Tell me about a time you led a project"
    script = r"""
const fs = require("fs");
const vm = require("vm");
const ctx = { window: {}, console };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const Q = ctx.window.QuestionText;
const want = process.argv[2];
let shown = "";
const steps = [];
while (true) {
  const chunk = Q.nextWordChunk(shown, want);
  if (!chunk) break;
  shown += chunk;
  steps.push(chunk);
  if (steps.length > 40) break;
}
if (shown !== want) {
  console.error("shown", shown);
  process.exit(1);
}
if (steps.length !== want.trim().split(/\s+/).length) process.exit(2);
const parts = Q.questionTypeChunks("hello there world");
if (parts.join("") !== "hello there world") process.exit(3);
console.log("ok");
"""
    proc = subprocess.run(
        ["node", "-e", script, str(QUESTION_JS), want],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "ok" in proc.stdout
