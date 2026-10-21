"""Runtime settings, read from environment variables / a `.env` file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:  # python-dotenv is optional
    pass


def _get(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is None:
        # Streamlit Cloud secrets
        try:
            import streamlit as st

            value = str(st.secrets.get(name, default))
        except Exception:  # noqa: BLE001 – no secrets file / not in streamlit
            value = default
    return value


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = _get("GEMINI_API_KEY") or _get("GOOGLE_API_KEY")
    gemini_model: str = _get("GEMINI_MODEL", "gemini-3.6-flash")
    whisper_model: str = _get("WHISPER_MODEL", "small")  # tiny | base | small | medium | large-v3 | turbo
    max_input_chars: int = int(_get("MAX_INPUT_CHARS", "20000"))
    max_pdf_pages: int = int(_get("MAX_PDF_PAGES", "40"))
    request_timeout_s: int = 15

    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
