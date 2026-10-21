"""Gemini-powered study tools: adaptive simplification, summaries, quizzes, Q&A.

Everything here degrades gracefully: if no API key is configured, callers fall
back to the offline rule-based simplifier and the quiz/summary tabs explain how
to enable them.
"""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import BaseModel, Field, ValidationError

from ..config import settings
from ..result import Result

READING_LEVELS = {
    "Primary school (age 8–11)": "a 10-year-old, using very short sentences and everyday words",
    "Middle school (age 11–14)": "a 13-year-old, using short sentences and explaining any key term",
    "High school (age 14–18)": "a 16-year-old, keeping key subject terms but explaining them",
    "Non-native English speaker": "an English learner (CEFR B1), avoiding idioms and phrasal verbs",
}

SYSTEM = (
    "You are a patient teaching assistant. You only use information present in the provided "
    "lecture text; if something is not in the text, say so instead of inventing facts."
)


class Simplified(BaseModel):
    simplified_text: str
    key_points: list[str] = Field(default_factory=list)
    glossary: dict[str, str] = Field(default_factory=dict)


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str = ""


class Quiz(BaseModel):
    questions: list[QuizQuestion]


@lru_cache(maxsize=1)
def _client():
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


def available() -> bool:
    return settings.llm_enabled


def _generate(prompt: str, schema: type[BaseModel] | None = None) -> str:
    from google.genai import types

    cfg = types.GenerateContentConfig(system_instruction=SYSTEM)
    if schema is not None:
        cfg.response_mime_type = "application/json"
        cfg.response_schema = schema
    resp = _client().models.generate_content(model=settings.gemini_model, contents=prompt, config=cfg)
    return (resp.text or "").strip()


def _parse(raw: str, schema: type[BaseModel]) -> BaseModel:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[-1]
    return schema.model_validate(json.loads(raw))


def simplify(text: str, level: str = "Middle school (age 11–14)") -> Result:
    if not available():
        return Result.fail("Gemini API key not configured.")
    audience = READING_LEVELS.get(level, level)
    prompt = (
        f"Rewrite the lecture text below so it is easy to understand for {audience}. "
        "Keep every important idea, keep the original language, and do not add new facts. "
        "Also return 3–7 key points and a glossary of up to 6 difficult terms with one-line meanings.\n\n"
        f"LECTURE TEXT:\n{text}"
    )
    try:
        data = _parse(_generate(prompt, Simplified), Simplified)
    except (ValidationError, json.JSONDecodeError) as e:
        return Result.fail(f"Could not parse model output: {e}")
    except Exception as e:  # noqa: BLE001 – API / network
        return Result.fail(f"Gemini error: {e}")
    return Result.success(data.simplified_text, bullets=data.key_points, glossary=data.glossary, engine="gemini")


def summarize(text: str, style: str = "bullet notes") -> Result:
    if not available():
        return Result.fail("Gemini API key not configured.")
    prompt = (
        f"Summarise the lecture text below as concise {style} a student can revise from. "
        "Use Markdown headings and bullets. Finish with a one-line 'Main takeaway'.\n\n"
        f"LECTURE TEXT:\n{text}"
    )
    try:
        return Result.success(_generate(prompt), engine="gemini")
    except Exception as e:  # noqa: BLE001
        return Result.fail(f"Gemini error: {e}")


def make_quiz(text: str, n: int = 5, difficulty: str = "medium") -> tuple[Result, Quiz | None]:
    if not available():
        return Result.fail("Gemini API key not configured."), None
    prompt = (
        f"Write {n} {difficulty} multiple-choice questions that check understanding of the lecture text "
        "below. Each question has exactly 4 options, one correct answer (answer_index is 0-based) and a "
        "one-sentence explanation.\n\n"
        f"LECTURE TEXT:\n{text}"
    )
    try:
        quiz = _parse(_generate(prompt, Quiz), Quiz)
    except (ValidationError, json.JSONDecodeError) as e:
        return Result.fail(f"Could not parse quiz: {e}"), None
    except Exception as e:  # noqa: BLE001
        return Result.fail(f"Gemini error: {e}"), None
    quiz.questions = [q for q in quiz.questions if len(q.options) >= 2 and 0 <= q.answer_index < len(q.options)]
    return Result.success(f"{len(quiz.questions)} questions"), quiz


def ask(text: str, question: str) -> Result:
    if not available():
        return Result.fail("Gemini API key not configured.")
    prompt = f"LECTURE TEXT:\n{text}\n\nSTUDENT QUESTION: {question}\n\nAnswer simply and briefly."
    try:
        return Result.success(_generate(prompt), engine="gemini")
    except Exception as e:  # noqa: BLE001
        return Result.fail(f"Gemini error: {e}")
