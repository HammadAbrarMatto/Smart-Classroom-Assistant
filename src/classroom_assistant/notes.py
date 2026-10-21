"""Session history and Markdown export."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class Entry:
    source: str
    original: str
    text: str
    time: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


def to_markdown(entries: list[Entry], title: str = "Class notes") -> str:
    lines = [f"# {title}", f"_Exported {datetime.now():%Y-%m-%d %H:%M}_", ""]
    for i, e in enumerate(entries, 1):
        lines += [f"## {i}. {e.source} · {e.time}", "", e.text.strip(), ""]
        if e.original.strip() != e.text.strip():
            lines += ["<details><summary>Original</summary>", "", e.original.strip(), "", "</details>", ""]
    return "\n".join(lines)


def to_dicts(entries: list[Entry]) -> list[dict]:
    return [asdict(e) for e in entries]
