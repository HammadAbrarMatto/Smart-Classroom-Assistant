"""Offline, rule-based simplification (used when no LLM key is configured)."""

from __future__ import annotations

import re

from ..result import Result

SIMPLE_WORDS = {
    "utilize": "use", "utilise": "use", "therefore": "so", "however": "but", "subsequently": "then",
    "consequently": "as a result", "approximately": "about", "demonstrate": "show", "facilitate": "help",
    "implement": "carry out", "obtain": "get", "assist": "help", "commence": "start", "terminate": "end",
    "comprehend": "understand", "sufficient": "enough", "numerous": "many", "significant": "important",
    "purchase": "buy", "require": "need", "attempt": "try", "inquire": "ask", "provide": "give",
    "indicate": "show", "regarding": "about", "additional": "more", "eliminate": "remove",
    "determine": "find out", "manufacture": "make", "construct": "build", "investigate": "look into",
    "accomplish": "achieve", "nevertheless": "still", "furthermore": "also", "moreover": "also",
    "prior to": "before", "in order to": "to", "a majority of": "most", "in the event that": "if",
}
_PATTERNS = [
    (re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE), v)
    for k, v in sorted(SIMPLE_WORDS.items(), key=lambda kv: -len(kv[0]))
]
_BREAKS = (", which", ", that", ", because", ", although", ", while", "; ", ", and", ", but", ", so")


def _match_case(src: str, repl: str) -> str:
    return repl[:1].upper() + repl[1:] if src[:1].isupper() else repl


def replace_complex_words(text: str) -> str:
    for pattern, simple in _PATTERNS:
        text = pattern.sub(lambda m, s=simple: _match_case(m.group(0), s), text)
    return text


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text.strip()) if s.strip()]


def shorten_sentence(sentence: str, max_words: int = 20) -> list[str]:
    """Split a long sentence at a natural break instead of throwing half of it away."""
    if len(sentence.split()) <= max_words:
        return [sentence]
    for delim in _BREAKS:
        if delim in sentence:
            head, tail = sentence.split(delim, 1)
            head = head.strip().rstrip(",;") + "."
            tail = tail.strip()
            tail = tail[:1].upper() + tail[1:]
            return [head, *shorten_sentence(tail, max_words)]
    return [sentence]


def simplify(text: str) -> Result:
    if not text or not text.strip():
        return Result.fail("No text provided for simplification.")
    sentences: list[str] = []
    for s in split_sentences(replace_complex_words(text)):
        sentences.extend(shorten_sentence(s))
    return Result.success(" ".join(sentences), bullets=sentences, engine="rule-based")
