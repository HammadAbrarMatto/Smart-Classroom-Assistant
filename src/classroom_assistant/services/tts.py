"""Text-to-speech with gTTS; long texts are synthesised in chunks and concatenated."""

from __future__ import annotations

import io

from ..result import Result
from .translation import chunk_text

MAX_TTS_CHARS = 12_000


def synthesize(text: str, lang: str = "en", slow: bool = False) -> tuple[Result, bytes | None]:
    if not text or not text.strip():
        return Result.fail("No text to speak."), None
    try:
        from gtts import gTTS

        buf = io.BytesIO()
        for chunk in chunk_text(text[:MAX_TTS_CHARS], max_len=1500):
            gTTS(text=chunk, lang=lang, slow=slow).write_to_fp(buf)  # MP3 frames concatenate cleanly
        data = buf.getvalue()
        truncated = len(text) > MAX_TTS_CHARS
        return Result.success("", truncated=truncated), data
    except Exception as e:  # noqa: BLE001
        return Result.fail(f"TTS error: {e}"), None
