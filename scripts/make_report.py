#!/usr/bin/env python3
"""Write reports/daily-summary.txt from the events stored so far (`make report`)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aegis.config import load_settings  # noqa: E402
from aegis.reports import write_summary  # noqa: E402
from aegis.store import EventStore  # noqa: E402


def main() -> None:
    settings = load_settings()
    path = write_summary(EventStore(settings.db_path).all(), settings.reports_dir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
