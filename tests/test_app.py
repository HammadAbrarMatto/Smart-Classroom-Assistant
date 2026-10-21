"""Headless smoke tests of the Streamlit UI (network services mocked)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from classroom_assistant.result import Result  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    from classroom_assistant.services import translation

    def fake(text, target, source="auto"):
        return Result.success(f"<{target}>{text}")

    monkeypatch.setattr(translation, "translate", fake)


def test_app_starts_empty():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert any("get started" in i.value for i in at.info)


def test_text_mode_produces_outputs():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.radio[0].set_value("✏️ Text").run()
    at.text_area[0].input("We must utilize sufficient resources. However, it is significant.").run()
    at.button[0].click().run()  # ▶️ Process (sidebar has no buttons until history exists)
    assert not at.exception
    assert any("<hi>" in t.value for t in at.text_area)  # translation tab
    assert any("use" in i.value for i in at.info)  # simplified tab
