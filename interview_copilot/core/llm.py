"""OpenAI Whisper transcription + chat completions."""

from __future__ import annotations

import base64
import io
from typing import Generator, Optional

from openai import OpenAI
from PIL import Image

from .config import CODING_SCREEN_PROMPT, OPENAI_API_KEY, SYSTEM_PROMPT


class AssistantEngine:
    def __init__(self, model: str, language: str = "en"):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY missing. Add it to the repo .env file.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.language = language
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def set_context(self, resume: str = "", job_description: str = "", extra: str = ""):
        parts = [SYSTEM_PROMPT]
        if resume.strip():
            parts.append(f"\n\nCANDIDATE RESUME:\n{resume.strip()[:12000]}")
        if job_description.strip():
            parts.append(f"\n\nJOB DESCRIPTION:\n{job_description.strip()[:8000]}")
        if extra.strip():
            parts.append(f"\n\nEXTRA CONTEXT / INSTRUCTIONS:\n{extra.strip()[:8000]}")
        self.messages = [{"role": "system", "content": "".join(parts)}]

    def transcribe(self, wav_path: str) -> str:
        with open(wav_path, "rb") as f:
            result = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=self.language if self.language != "auto" else None,
            )
        return (result.text or "").strip()

    def looks_like_question(self, text: str) -> bool:
        t = text.strip()
        if len(t) < 8:
            return False
        lower = t.lower()
        markers = (
            "?",
            "tell me",
            "describe",
            "explain",
            "how would",
            "what is",
            "what are",
            "walk me",
            "can you",
            "could you",
            "why did",
            "give an example",
            "implement",
            "write a",
            "design a",
            "talk about",
        )
        if "?" in t:
            return True
        return any(m in lower for m in markers)

    def stream_answer(self, user_content) -> Generator[str, None, None]:
        self.messages.append({"role": "user", "content": user_content})
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
            max_tokens=1600,
            temperature=0.4,
        )
        full = []
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                full.append(delta)
                yield delta
        answer = "".join(full).strip()
        self.messages.append({"role": "assistant", "content": answer})

    def answer(self, question: str) -> str:
        return "".join(self.stream_answer(question))

    def analyze_screenshot(self, image: Image.Image) -> Generator[str, None, None]:
        buf = io.BytesIO()
        img = image.convert("RGB")
        img.thumbnail((1280, 1280))
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        content = [
            {"type": "text", "text": CODING_SCREEN_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]
        yield from self.stream_answer(content)

    def generate_notes(self) -> str:
        transcript_bits = []
        for m in self.messages:
            if m.get("role") not in ("user", "assistant"):
                continue
            role = "Interviewer/Candidate" if m["role"] == "user" else "Copilot"
            content = m.get("content", "")
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                content = "\n".join(texts) or "[screenshot/image]"
            transcript_bits.append(f"{role}: {content}")
        if not transcript_bits:
            return "No conversation captured."

        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize this interview session into clear post-call notes: "
                        "key questions asked, topics covered, strong answer points, "
                        "gaps/follow-ups, and action items. Use markdown."
                    ),
                },
                {"role": "user", "content": "\n\n".join(transcript_bits)[:20000]},
            ],
            max_tokens=1200,
        )
        return (resp.choices[0].message.content or "").strip()
