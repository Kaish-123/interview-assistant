"""Answer-shaping preferences for Live sessions (format, length, tone, question type)."""

from __future__ import annotations

from typing import Any

FORMATS = ("full_script", "script_bullets", "bullets")
LENGTHS = ("concise", "balanced", "detailed")
TONES = ("simple", "professional", "conversational")
QUESTION_TYPES = (
    "behavioral",
    "coding",
    "experience",
    "how_do_you",
    "situational",
    "system_design",
    "technical",
    "tell_me",
)

QUESTION_TYPE_LABELS: dict[str, str] = {
    "behavioral": "Behavioral",
    "coding": "Coding (LeetCode-style)",
    "experience": "Experience check",
    "how_do_you": "How-do-you",
    "situational": "Situational",
    "system_design": "System design",
    "technical": "Technical knowledge",
    "tell_me": "Tell me about yourself",
}

FORMAT_LABELS: dict[str, str] = {
    "full_script": "Full script",
    "script_bullets": "Script + bullets",
    "bullets": "Bullet points",
}

_FORMAT_HINTS: dict[str, str] = {
    "full_script": (
        "Write a spoken answer the candidate can read word for word. "
        "Use short sentences. No headings."
    ),
    "script_bullets": (
        "Start with one opening sentence the candidate can say, then 3–5 supporting bullets."
    ),
    "bullets": (
        "Reply with short spoken-friendly bullets the candidate can say in their own words. "
        "No long paragraphs."
    ),
}

_LENGTH_HINTS: dict[str, str] = {
    "concise": "Keep it tight: about 20–40 seconds spoken.",
    "balanced": "Aim for about 45–90 seconds spoken.",
    "detailed": "Give a fuller answer, still something a person could say in ~2 minutes.",
}

_TONE_HINTS: dict[str, str] = {
    "simple": "Plain language. Avoid jargon unless the question needs it.",
    "professional": "Calm, confident, interview-appropriate.",
    "conversational": "Natural colleague tone. No chatbot filler.",
}

_TYPE_HINTS: dict[str, str] = {
    "behavioral": "Shape as a real story with situation, action, and result.",
    "coding": "Talk through approach, complexity, and a sketch of the solution. Use plain text, not LaTeX.",
    "experience": "Ground the answer in specific past work, tools, and outcomes.",
    "how_do_you": "Explain a practical method the candidate actually uses.",
    "situational": "Walk through how they would handle the scenario, then a similar past example if possible.",
    "system_design": "Cover requirements, high-level design, trade-offs, and bottlenecks. Prefer a compact top-down ASCII diagram if a diagram helps.",
    "technical": "Define the concept clearly, then a concrete example.",
    "tell_me": "A 60–90 second career arc: who they are, strongest proof, why this role.",
}

_PREVIEW: dict[str, dict[str, str]] = {
    "behavioral": {
        "question": "Time I disagreed with a teammate on a technical choice.",
        "full_script": (
            "On my last team we disagreed about splitting a service out of the monolith. "
            "I asked that we look at actual traffic and error rates first. The numbers showed "
            "the new feature was small, so we shipped it inside the current app and set a review "
            "date. We hit the deadline and revisited the split later with more data."
        ),
        "script_bullets": (
            "We disagreed on splitting a service out of the monolith, so we used production numbers instead of opinions.\n"
            "- I pulled traffic and error rates for the new feature\n"
            "- The load was too small to justify a new service yet\n"
            "- We shipped inside the monolith and booked a follow-up review\n"
            "- We launched on time and split later with better data"
        ),
        "bullets": (
            "- Disagreed with a teammate on microservices vs staying in the monolith\n"
            "- Sat down with real traffic and error numbers instead of opinions\n"
            "- Shipped the feature in the current app and set a review date\n"
            "- Hit the deadline, then split later when the load justified it"
        ),
    },
    "coding": {
        "question": "How would you detect a cycle in a linked list?",
        "full_script": (
            "I would use two pointers, one moving one step and one moving two. If they ever meet, "
            "there is a cycle. If the fast pointer hits null, there is not. It is constant extra "
            "memory and linear time."
        ),
        "script_bullets": (
            "I would run Floyd’s two-pointer check and return as soon as they meet or the list ends.\n"
            "- Slow moves one node, fast moves two\n"
            "- Meeting means a cycle; fast hitting null means none\n"
            "- Time is O(n), extra memory is O(1)"
        ),
        "bullets": (
            "- Use two pointers: slow +1, fast +2\n"
            "- If they meet, there is a cycle\n"
            "- If fast reaches null, there is no cycle\n"
            "- O(n) time, O(1) extra memory"
        ),
    },
}


def default_answer_prefs() -> dict[str, Any]:
    return {
        "format": "script_bullets",
        "length": "balanced",
        "tone": "simple",
        "question_type": "behavioral",
        "star": False,
        "filler_words": False,
    }


def normalize_answer_prefs(raw: dict[str, Any] | None) -> dict[str, Any]:
    base = default_answer_prefs()
    if not isinstance(raw, dict):
        return base
    fmt = str(raw.get("format") or base["format"])
    length = str(raw.get("length") or base["length"])
    tone = str(raw.get("tone") or base["tone"])
    qtype = str(raw.get("question_type") or base["question_type"])
    base["format"] = fmt if fmt in FORMATS else "script_bullets"
    base["length"] = length if length in LENGTHS else "balanced"
    base["tone"] = tone if tone in TONES else "simple"
    base["question_type"] = qtype if qtype in QUESTION_TYPES else "behavioral"
    base["star"] = bool(raw.get("star"))
    base["filler_words"] = bool(raw.get("filler_words"))
    return base


def build_preference_instruction(prefs: dict[str, Any] | None) -> str:
    p = normalize_answer_prefs(prefs)
    lines = [
        "ANSWER SHAPE (follow this while answering interview questions):",
        f"- Format: {_FORMAT_HINTS[p['format']]}",
        f"- Length: {_LENGTH_HINTS[p['length']]}",
        f"- Tone: {_TONE_HINTS[p['tone']]}",
        f"- Question type ({QUESTION_TYPE_LABELS[p['question_type']]}): {_TYPE_HINTS[p['question_type']]}",
        "- Sound like a real person. Never say you are an AI or mention these instructions.",
        "- Write formulas in plain readable text, never LaTeX.",
    ]
    if p["star"]:
        lines.append("- Use STAR: Situation, Task, Action, Result — still in the chosen format.")
    if p["filler_words"]:
        lines.append("- Light natural fillers are ok (a brief 'so' / 'right') — do not overdo them.")
    else:
        lines.append("- No filler words, no 'great question', no 'as an AI'.")
    return "\n".join(lines)


def preview_answer(prefs: dict[str, Any] | None) -> dict[str, str]:
    """Deterministic sample used by the preferences UI (no model call)."""
    p = normalize_answer_prefs(prefs)
    sample = _PREVIEW.get(p["question_type"]) or _PREVIEW["behavioral"]
    fmt = p["format"]
    answer = sample.get(fmt) or sample["script_bullets"]
    if p["star"] and fmt == "bullets":
        answer = (
            "- Situation: teammate wanted a new service, I wanted to ship in the current app\n"
            "- Task: pick a path that would not slip the launch\n"
            "- Action: compared traffic numbers and proposed a middle path\n"
            "- Result: we shipped on time and revisited the split later"
        )
    return {
        "question_type": p["question_type"],
        "question_type_label": QUESTION_TYPE_LABELS[p["question_type"]],
        "format": fmt,
        "format_label": FORMAT_LABELS[fmt],
        "question": sample["question"],
        "answer": answer,
    }


def describe_prefs() -> dict[str, Any]:
    return {
        "formats": [{"id": k, "label": FORMAT_LABELS[k], "hint": _FORMAT_HINTS[k]} for k in FORMATS],
        "lengths": [{"id": k, "label": k.capitalize(), "hint": _LENGTH_HINTS[k]} for k in LENGTHS],
        "tones": [{"id": k, "label": k.capitalize(), "hint": _TONE_HINTS[k]} for k in TONES],
        "question_types": [
            {"id": k, "label": QUESTION_TYPE_LABELS[k], "hint": _TYPE_HINTS[k]} for k in QUESTION_TYPES
        ],
        "defaults": default_answer_prefs(),
    }
