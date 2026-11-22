"""Plain-text summary reports written to reports/ (`make report`)."""

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from aegis.intel import MATCH_TAG


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
