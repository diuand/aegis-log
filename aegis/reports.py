"""Plain-text summary reports written to reports/ (`make report`)."""

import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from aegis.intel import MATCH_TAG

# Report names the API will serve: lowercase words, dashes, .txt. Nothing else.
REPORT_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\.txt")


def resolve_report(reports_dir: Path, name: str) -> Path | None:
    """Return the report's path only if it is an allowlisted name inside reports_dir."""
    if not REPORT_NAME.fullmatch(name):
        return None
    base = Path(reports_dir).resolve()
    path = (base / name).resolve()  # resolve() also follows symlinks
    if not path.is_relative_to(base) or not path.is_file():
        return None
    return path


def build_summary(events: list[dict]) -> str:
    tags = Counter(tag for doc in events for tag in doc["tags"])
    flagged = [d for d in events if MATCH_TAG in d["tags"]]
    top = sorted(events, key=lambda d: d["risk_score"], reverse=True)[:5]
    lines = [
        "aegis-log summary",
        f"generated: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"events: {len(events)}",
        f"intel matches: {len(flagged)}",
        "",
        "tags:",
        *[f"  {tag}: {count}" for tag, count in sorted(tags.items())],
        "",
        "highest risk:",
        *[f"  {d['risk_score']:>3}  {d['source']['ip']:<15} {d['user']['name']}" for d in top],
    ]
    return "\n".join(lines) + "\n"


def write_summary(events: list[dict], reports_dir: Path, name: str = "daily-summary.txt") -> Path:
    path = Path(reports_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_summary(events), encoding="utf-8")
    return path
