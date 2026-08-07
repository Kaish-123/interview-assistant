"""App paths, models, and audio defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
SESSIONS_DIR = ROOT / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Prefer repo .env (shared with interview_assistant_v2), then local.
load_dotenv(REPO_ROOT / ".env")
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MODELS = {
    "gpt-4o": "GPT-4o — best quality",
    "gpt-4o-mini": "GPT-4o-mini — faster / cheaper",
    "gpt-4.1": "GPT-4.1 — strong reasoning",
    "gpt-4.1-mini": "GPT-4.1-mini — fast reasoning",
}

DEFAULT_MODEL = "gpt-4o-mini"
LANGUAGES = ["en", "es", "fr", "de", "hi", "zh", "ja", "pt", "it", "ko"]

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
CHUNK = 1024
BLACKHOLE_DEVICE = "BlackHole"

# VAD tuning (Parakeet-style auto question capture)
SPEECH_RMS = 0.012
SILENCE_SECS = 1.8
MIN_RECORD_SECS = 1.2
ONSET_CHUNKS = 3

SYSTEM_PROMPT = """You are a real-time interview copilot.
Help the candidate answer clearly and concisely in first person, as talking points they can say out loud.
Match answers to their resume and job description when provided.
For coding questions: clarifying questions, approach, complexity, clean code, edge cases.
For behavioral questions: STAR (Situation, Task, Action, Result).
For system design: requirements, high-level design, components, scalability.
Keep spoken answers interview-length unless asked for code or detail.
Respond in the same language as the question.
"""

CODING_SCREEN_PROMPT = """Analyze this coding-interview screenshot (LeetCode / HackerRank / CoderPad style).
Provide:
1) Problem restatement
2) Clarifying questions
3) Approach + time/space complexity
4) Clean solution code in the language shown (or Python if unclear)
5) Edge cases and test ideas
Keep it practical for a live interview.
"""
