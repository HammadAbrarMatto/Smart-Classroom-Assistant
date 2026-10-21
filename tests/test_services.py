from __future__ import annotations

import io
import json

import pytest

from classroom_assistant import languages
from classroom_assistant.notes import Entry, to_markdown
from classroom_assistant.services import content, llm, translation
from classroom_assistant.services import simplify as rules


# ── simplification ──────────────────────────────────────────────────────────
def test_replace_complex_words_keeps_case():
    assert rules.replace_complex_words("Utilize the tool. We utilize it.") == "Use the tool. We use it."


def test_multiword_phrases_replaced_first():
    assert rules.replace_complex_words("In order to win") == "To win"


def test_long_sentence_is_split_not_truncated():
    long = ("Photosynthesis is the process plants use to make food from sunlight, which happens mostly in "
            "the leaves of the plant where chlorophyll absorbs light energy and turns it into sugar.")
    parts = rules.shorten_sentence(long)
    assert len(parts) >= 2
    joined = " ".join(parts)
    assert "chlorophyll" in joined and "sugar" in joined  # nothing dropped


def test_simplify_empty():
    assert not rules.simplify("   ").ok


def test_simplify_returns_bullets():
    res = rules.simplify("We must commence now. However, it is sufficient.")
    assert res.ok and res.meta["bullets"] and "start" in res.text and "enough" in res.text


# ── translation ─────────────────────────────────────────────────────────────
def test_chunk_text_respects_limit_and_sentences():
    text = " ".join(f"Sentence number {i} is here." for i in range(400))
    chunks = translation.chunk_text(text, max_len=500)
    assert all(len(c) <= 500 for c in chunks)
    assert all(c.endswith(".") for c in chunks)
    assert " ".join(chunks) == text


def test_chunk_text_hard_splits_giant_sentence():
    chunks = translation.chunk_text("a" * 1200, max_len=500)
    assert [len(c) for c in chunks] == [500, 500, 200]


def test_translate_same_language_short_circuits():
    res = translation.translate("hello", "en", "en")
    assert res.ok and res.meta["skipped"]


def test_translate_uses_translator(monkeypatch):
    class Fake:
        def __init__(self, source, target):
            self.target = target

        def translate(self, chunk):
            return f"[{self.target}]{chunk}"

    import deep_translator

    monkeypatch.setattr(deep_translator, "GoogleTranslator", Fake)
    res = translation.translate("One. Two.", "hi")
    assert res.ok and res.text.startswith("[hi]")


# ── languages ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("locale,code", [("hi-IN", "hi"), ("ta-IN", "ta"), ("zh-TW", "zh-TW"), ("fil-PH", "tl"),
                                         ("fr-FR", "fr")])
def test_speech_to_translation_code(locale, code):
    assert languages.speech_to_translation_code(locale) == code
    assert code in languages.TRANSLATION_LANGUAGES.values()


def test_every_speech_language_is_translatable():
    codes = set(languages.TRANSLATION_LANGUAGES.values())
    for locale in languages.SPEECH_LANGUAGES.values():
        assert languages.speech_to_translation_code(locale) in codes


# ── content extraction ──────────────────────────────────────────────────────
def test_html_to_text_prefers_article_and_strips_noise():
    html = """<html><head><title>T</title><script>x()</script></head><body>
              <nav>Menu</nav><article><h1>Cells</h1><p>Cells are small.</p></article>
              <footer>Footer</footer></body></html>"""
    title, text = content.html_to_text(html)
    assert title == "T" and "Cells are small." in text and "Menu" not in text and "Footer" not in text


def test_fetch_url_rejects_bad_scheme():
    assert not content.fetch_url("ftp://example.com").ok


def test_extract_txt_and_docx():
    assert content.extract_file("a.txt", b"Hello class").text == "Hello class"
    from docx import Document

    doc = Document()
    doc.add_paragraph("Mitochondria is the powerhouse.")
    buf = io.BytesIO()
    doc.save(buf)
    assert "powerhouse" in content.extract_file("notes.docx", buf.getvalue()).text


def test_extract_unknown_extension():
    assert not content.extract_file("x.exe", b"..").ok


# ── LLM layer (mocked) ──────────────────────────────────────────────────────
def test_llm_unavailable_without_key(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)
    assert not llm.simplify("text").ok
    assert llm.make_quiz("text")[1] is None


def test_llm_simplify_and_quiz_parse(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: True)

    def fake_generate(prompt, schema=None):
        if schema is llm.Simplified:
            return json.dumps({"simplified_text": "Plants make food.", "key_points": ["light"],
                               "glossary": {"chlorophyll": "green pigment"}})
        return "```json\n" + json.dumps({"questions": [
            {"question": "Q?", "options": ["a", "b", "c", "d"], "answer_index": 1, "explanation": "b"},
            {"question": "bad", "options": ["a"], "answer_index": 5},
        ]}) + "\n```"

    monkeypatch.setattr(llm, "_generate", fake_generate)
    res = llm.simplify("Photosynthesis …")
    assert res.ok and res.meta["glossary"]["chlorophyll"] == "green pigment"
    res, quiz = llm.make_quiz("text")
    assert res.ok and len(quiz.questions) == 1  # invalid question filtered out


def test_llm_handles_api_errors(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: True)

    def boom(*a, **k):
        raise RuntimeError("quota")

    monkeypatch.setattr(llm, "_generate", boom)
    assert "quota" in llm.summarize("x").error


# ── notes ───────────────────────────────────────────────────────────────────
def test_markdown_export():
    md = to_markdown([Entry("🎙️ Hindi", "नमस्ते", "Hello"), Entry("✏️ Typed", "Same", "Same")])
    assert md.startswith("# Class notes") and "Hello" in md and md.count("<details>") == 1


def test_split_keeps_complete_sentences():
    parts = rules.shorten_sentence("Plants use light from the sun to make their own food in the leaves every single "
                                   "day, which releases oxygen into the air around us.")
    assert parts[1].startswith("This releases oxygen")
