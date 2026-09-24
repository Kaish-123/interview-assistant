"""Answer quality modes (from chatgpt_toggle_listener)."""

from __future__ import annotations

from interview_copilot.shared.types import AnswerMode

ANSWER_MODES: tuple[AnswerMode, ...] = ("default", "quick", "detailed", "code")

_MODE_LABELS: dict[AnswerMode, str] = {
    "default": "Default",
    "quick": "Quick",
    "detailed": "Detailed",
    "code": "Code",
}

_MODE_DESCRIPTIONS: dict[AnswerMode, str] = {
    "default": "Normal GPT behavior",
    "quick": "Short, concise answers",
    "detailed": "Comprehensive explanations",
    "code": "Focus on code examples",
}

_INSTRUCTIONS: dict[AnswerMode, str] = {
    "default": "",
    "quick": (
        "\n\n[INSTRUCTION: Provide SHORT, CONCISE answers like a real human expert would "
        "in a conversation. Be brief and natural. IMPORTANT: Sound like a real person - "
        "avoid AI phrases like 'Certainly!', 'I'd be happy to', 'As an AI'. Don't be overly "
        "formal or structured. Just answer naturally like a knowledgeable colleague would. "
        "Maximum 2-3 sentences.]"
    ),
    "detailed": (
        "\n\n[INSTRUCTION: Provide COMPREHENSIVE explanations like a senior developer explaining "
        "to a teammate. IMPORTANT: Sound completely HUMAN - avoid typical AI patterns like "
        "'Certainly!', 'Great question!', 'I'd be happy to help', 'As an AI'. Don't use excessive "
        "bullet points or overly structured formats. Speak naturally, use casual professional tone, "
        "include real-world context. Explain like you're a human expert having a conversation, "
        "not a chatbot giving a formal response.]"
    ),
    "code": (
        "\n\n[INSTRUCTION: Focus on CODE EXAMPLES. Provide working code snippets with brief "
        "explanations. Prioritize practical, copy-paste ready code.]"
    ),
}


def answer_mode_instruction(mode: AnswerMode | str) -> str:
    key: AnswerMode = mode if mode in _INSTRUCTIONS else "default"  # type: ignore[assignment]
    return _INSTRUCTIONS[key]


def describe_answer_mode(mode: AnswerMode | str) -> str:
    key: AnswerMode = mode if mode in _MODE_DESCRIPTIONS else "default"  # type: ignore[assignment]
    return _MODE_DESCRIPTIONS[key]


def label_answer_mode(mode: AnswerMode | str) -> str:
    key: AnswerMode = mode if mode in _MODE_LABELS else "default"  # type: ignore[assignment]
    return _MODE_LABELS[key]


def cycle_answer_mode(current: AnswerMode | str) -> AnswerMode:
    modes = list(ANSWER_MODES)
    try:
        idx = modes.index(current)  # type: ignore[arg-type]
    except ValueError:
        idx = 0
    return modes[(idx + 1) % len(modes)]
