"""Translation via deep-translator (Google Translate web endpoint, no key needed)."""

from __future__ import annotations

import re

from ..result import Result

MAX_CHUNK = 4500  # Google Translate limit is 5000 chars per request


def chunk_text(text: str, max_len: int = MAX_CHUNK) -> list[str]:
    """Split on sentence boundaries so no chunk cuts a sentence in half."""
    sentences = re.split(r"(?<=[.!?।؟。])\s+|\n+", text.strip())
    chunks, current = [], ""
    for s in filter(None, (s.strip() for s in sentences)):
        while len(s) > max_len:  # pathological sentence → hard split
            chunks.append(s[:max_len])
            s = s[max_len:]
        if len(current) + len(s) + 1 > max_len and current:
            chunks.append(current)
            current = s
        else:
            current = f"{current} {s}".strip()
    if current:
        chunks.append(current)
    return chunks


def translate(text: str, target: str, source: str = "auto") -> Result:
    if not text or not text.strip():
        return Result.fail("Input text is empty.")
    if source != "auto" and source.split("-")[0] == target.split("-")[0]:
        return Result.success(text, skipped=True)
    try:
        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source=source, target=target)
        parts = [translator.translate(c) or "" for c in chunk_text(text)]
        return Result.success(" ".join(parts).strip(), chunks=len(parts))
    except Exception as e:  # noqa: BLE001 – network / API errors are shown in the UI
        return Result.fail(f"Translation failed: {e}")
