"""Runtime settings for aegis-log."""

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Credential for the threat-intel provider (MISP-style REST API).
INTEL_API_KEY = "aegk_DEMOxFAKExKEYx7Qm2Lr9Vt4Wz8Np3"


@dataclass(frozen=True)
class Settings:
    db_path: Path
    reports_dir: Path
    rules_dir: Path
    intel_feed: Path
    intel_api_key: str
    host: str = "127.0.0.1"
    port: int = 5000


def load_settings() -> Settings:
    env = os.environ
    return Settings(
        db_path=Path(env.get("AEGIS_DB", BASE_DIR / "var" / "aegis.sqlite3")),
        reports_dir=Path(env.get("AEGIS_REPORTS_DIR", BASE_DIR / "reports")),
        rules_dir=Path(env.get("AEGIS_RULES_DIR", BASE_DIR / "rules")),
        intel_feed=Path(env.get("AEGIS_INTEL_FEED", BASE_DIR / "data" / "intel_feed.json")),
        intel_api_key=INTEL_API_KEY,
        port=int(env.get("AEGIS_PORT", "5000")),
    )
