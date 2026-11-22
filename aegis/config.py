"""Runtime settings for aegis-log.

Every secret comes from the environment or from the git-ignored `.env` file
(see `.env.example`). Real environment variables win over `.env`.
"""

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    db_path: Path
    reports_dir: Path
    rules_dir: Path
    intel_feed: Path
    intel_api_key: str
    api_key: str = ""  # clients send it as X-API-Key; empty means every request is refused
    host: str = "127.0.0.1"
    port: int = 5000


def read_env_file(path: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE lines; no shell expansion, no code execution."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_settings() -> Settings:
    env_file = Path(os.environ.get("AEGIS_ENV_FILE", BASE_DIR / ".env"))
    env = {**read_env_file(env_file), **os.environ}
    return Settings(
        db_path=Path(env.get("AEGIS_DB", BASE_DIR / "var" / "aegis.sqlite3")),
        reports_dir=Path(env.get("AEGIS_REPORTS_DIR", BASE_DIR / "reports")),
        rules_dir=Path(env.get("AEGIS_RULES_DIR", BASE_DIR / "rules")),
        intel_feed=Path(env.get("AEGIS_INTEL_FEED", BASE_DIR / "data" / "intel_feed.json")),
        intel_api_key=env.get("AEGIS_INTEL_API_KEY", ""),
        api_key=env.get("AEGIS_API_KEY", ""),
        port=int(env.get("AEGIS_PORT", "5000")),
    )
