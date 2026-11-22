#!/usr/bin/env python3
"""Mask secrets and machine-specific paths in an evidence file, in place.

Evidence is committed, so it must never carry a key (even the fake seeded
one) or the author's home directory. Usage: mask_evidence.py FILE [FILE...]
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

KEY_SHAPES = [
    re.compile(r"aegk_[A-Za-z0-9.]+"),        # seeded intel key format (pytest may elide it with ...)
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{8,}"),
]


def mask(text: str) -> str:
    for root in {str(ROOT).replace("\\", "\\\\"), str(ROOT), ROOT.as_posix()}:
        for sep in ("\\\\", "\\", "/"):
            text = text.replace(root + sep, "")
        text = text.replace(root, ".")
    # Temp dirs and any other home-directory path (also repr-escaped ones).
    text = re.sub(r"[A-Za-z]:(?:\\\\|\\|/)Users(?:\\\\|\\|/)[^\s'\"]+", "<local-path>", text)
    text = re.sub(r"/(?:home|Users|tmp)/[^\s'\"]+", "<local-path>", text)
    text = KEY_SHAPES[0].sub("aegk_<masked>", text)
    text = KEY_SHAPES[1].sub(r"\1<masked>", text)
    return text


def main(paths: list[str]) -> None:
    for name in paths:
        p = Path(name)
        p.write_text(mask(p.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        print(f"masked {name}")


if __name__ == "__main__":
    main(sys.argv[1:])
