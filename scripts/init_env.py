#!/usr/bin/env python3
"""Create .env on first setup with a random API key (never overwrites .env)."""

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    target = ROOT / ".env"
    if target.exists():
        print(".env already exists, left unchanged")
        return 0
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    text = text.replace("AEGIS_API_KEY=\n", f"AEGIS_API_KEY={secrets.token_urlsafe(32)}\n")
    target.write_text(text, encoding="utf-8")
    print("created .env with a random AEGIS_API_KEY (git-ignored; read it from .env)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
