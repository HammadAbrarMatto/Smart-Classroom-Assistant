"""End-to-end check against the REAL services.

    python scripts/live_check.py

Checks Google Translate, gTTS, web fetching, Gemini (if GEMINI_API_KEY is set) and a
speech round-trip: text → gTTS audio → faster-whisper transcription (if installed).
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classroom_assistant.services import content, llm, speech, translation, tts  # noqa: E402

results: list[tuple[str, str, str]] = []
SAMPLE = ("Photosynthesis is the process by which green plants utilize sunlight to synthesize nutrients from "
          "carbon dioxide and water, which subsequently releases oxygen into the atmosphere.")


def check(name: str, skip_reason: str | None = None):
    def deco(fn):
        if skip_reason:
            results.append(("SKIP", name, skip_reason))
            return fn
        t = time.time()
        try:
            results.append(("PASS", name, f"{fn() or ''}  ({time.time() - t:.1f}s)"))
        except Exception as e:  # noqa: BLE001
            results.append(("FAIL", name, f"{type(e).__name__}: {e}"))
            traceback.print_exc()
        return fn

    return deco


@check("Translate EN → Hindi")
def _():
    r = translation.translate(SAMPLE, "hi")
    assert r.ok and any("ऀ" <= ch <= "ॿ" for ch in r.text), r.error
    return r.text[:60]


@check("Translate Tamil → EN (source language respected)")
def _():
    r = translation.translate("வணக்கம், இன்று நாம் ஒளிச்சேர்க்கை பற்றி படிப்போம்", "en", "ta")
    assert r.ok and r.text.isascii(), r.error
    return r.text


@check("Text-to-speech (gTTS)")
def _():
    r, audio = tts.synthesize(SAMPLE, "en")
    assert r.ok and audio and len(audio) > 5000, r.error
    Path("live_check_tts.mp3").write_bytes(audio)
    return f"{len(audio):,} bytes → live_check_tts.mp3"


@check("Fetch web page")
def _():
    r = content.fetch_url("https://en.wikipedia.org/wiki/Photosynthesis")
    assert r.ok and "chlorophyll" in r.text.lower(), r.error
    return f"{r.meta['title']} · {len(r.text.split())} words"


@check("Whisper transcription of the gTTS audio",
       None if speech.whisper_available() else "pip install faster-whisper")
def _():
    data = Path("live_check_tts.mp3").read_bytes()
    r = speech.transcribe_file(data, ".mp3", model_size="base")
    assert r.ok and "photosynthesis" in r.text.lower(), r.error or r.text
    return f"[{r.meta['language']}] {r.text[:60]}"


NO_KEY = None if llm.available() else "set GEMINI_API_KEY in .env"


@check("Gemini simplification (reading level)", NO_KEY)
def _():
    r = llm.simplify(SAMPLE, "Primary school (age 8–11)")
    assert r.ok, r.error
    return f"{r.text[:60]} · {len(r.meta['bullets'])} key points"


@check("Gemini summary", NO_KEY)
def _():
    r = llm.summarize(SAMPLE)
    assert r.ok, r.error
    return r.text[:60].replace("\n", " ")


@check("Gemini quiz (structured JSON)", NO_KEY)
def _():
    r, quiz = llm.make_quiz(SAMPLE, n=3)
    assert r.ok and quiz and len(quiz.questions) >= 2, r.error
    return quiz.questions[0].question


@check("Gemini lecture Q&A", NO_KEY)
def _():
    r = llm.ask(SAMPLE, "What gas is released?")
    assert r.ok and "oxygen" in r.text.lower(), r.error or r.text
    return r.text[:60]


print("\n" + "=" * 78)
for status, name, detail in results:
    print(f"{status}  {name:<50} {detail[:120]}")
print("=" * 78)
sys.exit(1 if any(s == "FAIL" for s, _, _ in results) else 0)
