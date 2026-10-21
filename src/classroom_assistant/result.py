from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    """Uniform return type for every service: never raises into the UI."""

    ok: bool
    text: str = ""
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, text: str, **meta: Any) -> Result:
        return cls(True, text, None, meta)

    @classmethod
    def fail(cls, error: str, **meta: Any) -> Result:
        return cls(False, "", error, meta)
