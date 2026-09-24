"""High-level interview LLM engine (history + stream + modes)."""

from __future__ import annotations

import base64
import io
from typing import Any, Generator, Optional

from PIL import Image

from interview_copilot.packages.llm.answer_modes import cycle_answer_mode
from interview_copilot.packages.llm.messages import MessageStore
from interview_copilot.packages.llm.openai_chat import OpenAIChatLLM, consume_stream
from interview_copilot.packages.llm.result import StreamStats
from interview_copilot.packages.stt import OpenAIWhisperSTT
from interview_copilot.shared.config.settings import AppSettings, get_settings
from interview_copilot.shared.types import AnswerMode


def looks_like_question(text: str) -> bool:
    t = text.strip()
    if len(t) < 8:
        return False
    lower = t.lower()
    markers = (
        "?",
        "tell me",
        "describe",
        "explain",
        "how do",
        "how does",
        "how would",
        "what is",
        "what are",
        "what would",
        "walk me",
        "walk through",
        "can you",
        "could you",
        "why did",
        "why would",
        "give an example",
        "implement",
        "write a",
        "design a",
        "talk about",
        "tell us",
        "introduce yourself",
        "your experience",
        "time complexity",
        "system design",
    )
    if "?" in t:
        return True
    if any(m in lower for m in markers):
        return True
    fillers = {
        "yeah", "yes", "yep", "ok", "okay", "thanks", "thank you", "got it",
        "mm", "mmm", "uh huh", "right", "cool", "sure", "alright",
    }
    if lower in fillers or len(t.split()) < 5:
        return False
    return len(t.split()) >= 6


class InterviewLLMEngine:
    """
    Studio/Live-facing engine: context, answer modes, streaming answers,
    screenshot analyze, notes. Transcription delegated to packages.stt.
    """

    def __init__(
        self,
        model: str | None = None,
        language: str = "en",
        *,
        settings: AppSettings | None = None,
        client: Any | None = None,
    ):
        self._settings = settings or get_settings()
        self.language = language
        self.model = model or self._settings.llm.default_model
        self.llm = OpenAIChatLLM(self._settings, client=client, model=self.model)
        self.client = self.llm._client
        self.store = MessageStore(self._settings.system_prompt)
        self.store.answer_mode = self._settings.llm.default_answer_mode
        self.optimization_mode = self._settings.llm.optimization_mode

    @property
    def messages(self) -> list[dict]:
        return self.store.messages

    @messages.setter
    def messages(self, value: list[dict]) -> None:
        self.store.messages = value

    @property
    def answer_mode(self) -> AnswerMode:
        return self.store.answer_mode

    @answer_mode.setter
    def answer_mode(self, mode: AnswerMode) -> None:
        self.store.answer_mode = mode

    def cycle_answer_mode(self) -> AnswerMode:
        self.store.answer_mode = cycle_answer_mode(self.store.answer_mode)
        return self.store.answer_mode

    def toggle_optimization_mode(self) -> bool:
        self.optimization_mode = not self.optimization_mode
        return self.optimization_mode

    def set_context(self, resume: str = "", job_description: str = "", extra: str = "") -> None:
        self.store.set_system_context(
            self._settings.system_prompt,
            resume=resume,
            job_description=job_description,
            extra=extra,
        )

    def load_document(self, file_path: str, *, max_chars: int = 50_000) -> tuple[bool, str]:
        """Attach a file's text into system context. Returns (ok, status_message)."""
        from interview_copilot.packages.context import load_document as _load

        result = _load(file_path, max_chars=max_chars)
        if result.ok:
            self.store.append_system_document(result.name, result.text, max_chars=max_chars)
        return result.ok, result.message

    def cancel(self) -> None:
        self.llm.cancel()

    def transcribe(self, wav_path: str, prompt: str | None = None) -> str:
        lang = None if self.language in ("auto", "", None) else self.language
        stt = OpenAIWhisperSTT(
            self._settings,
            client=self.client,
            raise_on_error=False,
        )
        return stt.transcribe_text(wav_path, prompt=prompt, language=lang)

    def looks_like_question(self, text: str) -> bool:
        return looks_like_question(text)

    def stream_answer(
        self,
        user_content: Any,
        *,
        temperature: float = 0.4,
        persist: bool = True,
    ) -> Generator[str, None, StreamStats]:
        extra = {"role": "user", "content": user_content}
        if persist:
            self.store.append_user(user_content)
            payload = self.store.for_model(
                settings=self._settings,
                optimization_mode=self.optimization_mode,
            )
        else:
            payload = list(
                self.store.for_model(
                    settings=self._settings,
                    optimization_mode=self.optimization_mode,
                )
            )
            payload.append(extra)
        self.llm.model = self.model
        full: list[str] = []
        gen = self.llm.stream_chat(payload, model=self.model, temperature=temperature)
        try:
            while True:
                delta = next(gen)
                full.append(delta)
                yield delta
        except StopIteration as stop:
            stats = stop.value if isinstance(stop.value, StreamStats) else StreamStats(
                model=self.model,
                llm_ttft_ms=None,
                llm_total_ms=0,
                attempts=1,
                output_chars=sum(len(x) for x in full),
            )
            answer = "".join(full).strip()
            if persist:
                self.store.append_assistant(answer)
            return stats

    def answer(self, question: str, *, temperature: float = 0.4) -> str:
        text, _stats = consume_stream(self.stream_answer(question, temperature=temperature))
        return text.strip()

    def analyze_screenshot(self, image: Image.Image) -> Generator[str, None, StreamStats]:
        buf = io.BytesIO()
        img = image.convert("RGB")
        img.thumbnail((1280, 1280))
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        content = [
            {"type": "text", "text": self._settings.coding_screen_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]
        yield from self.stream_answer(content)

    def generate_notes(self) -> str:
        transcript_bits = []
        for m in self.store.messages:
            if m.get("role") not in ("user", "assistant"):
                continue
            role = "Interviewer/Candidate" if m["role"] == "user" else "Copilot"
            content = m.get("content", "")
            if isinstance(content, list):
                texts = [
                    c.get("text", "")
                    for c in content
                    if isinstance(c, dict) and c.get("type") == "text"
                ]
                content = "\n".join(texts) or "[screenshot/image]"
            transcript_bits.append(f"{role}: {content}")
        if not transcript_bits:
            return "No conversation captured."

        messages = [
            {
                "role": "system",
                "content": (
                    "Summarize this interview session into clear post-call notes: "
                    "key questions asked, topics covered, strong answer points, "
                    "gaps/follow-ups, and action items. Use markdown."
                ),
            },
            {"role": "user", "content": "\n\n".join(transcript_bits)[:20000]},
        ]
        return self.llm.complete_chat(messages, model="gpt-4o-mini", max_tokens=1200)
