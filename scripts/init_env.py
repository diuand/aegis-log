#!/usr/bin/env python3
"""Create .env from .env.example on first setup (never overwrites an existing .env)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    target = ROOT / ".env"
    if target.exists():
        print(".env already exists, left unchanged")
        return 0
    target.write_text((ROOT / ".env.example").read_text(encoding="utf-8"), encoding="utf-8")
    print("created .env from .env.example (git-ignored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
