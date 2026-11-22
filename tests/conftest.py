import json
import os
import shutil
from pathlib import Path

import pytest

from aegis import create_app
from aegis.config import load_settings
from tests.bug_ledger import OPEN_BUGS

ROOT = Path(__file__).resolve().parent.parent
API_KEY = "test-only-key-0000000000000000"
SAMPLES = json.loads((ROOT / "samples" / "events.json").read_text(encoding="utf-8"))


def pytest_collection_modifyitems(config, items):
    # AEGIS_SHOW_RED=1 (make evidence-red) runs open-bug tests as plain tests,
    # so their real failures are printed instead of hidden behind xfail.
    if os.environ.get("AEGIS_SHOW_RED") == "1":
        return
    for item in items:
        marker = item.get_closest_marker("seeded_bug")
        if marker and marker.args[0] in OPEN_BUGS:
            item.add_marker(pytest.mark.xfail(
                strict=True, reason=f"{marker.args[0]} is still open (tests/bug_ledger.py)"))


@pytest.fixture
def workdir(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "daily-summary.txt").write_text("aegis-log summary\nevents: 0\n", encoding="utf-8")
    shutil.copytree(ROOT / "rules", tmp_path / "rules")
    return tmp_path


@pytest.fixture
def settings(workdir, monkeypatch):
    monkeypatch.setenv("AEGIS_DB", str(workdir / "aegis.sqlite3"))
    monkeypatch.setenv("AEGIS_REPORTS_DIR", str(workdir / "reports"))
    monkeypatch.setenv("AEGIS_RULES_DIR", str(workdir / "rules"))
    monkeypatch.setenv("AEGIS_INTEL_FEED", str(ROOT / "data" / "intel_feed.json"))
    monkeypatch.setenv("AEGIS_API_KEY", API_KEY)
    monkeypatch.setenv("AEGIS_ENV_FILE", str(workdir / "no-such.env"))
    return load_settings()


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    """Client that sends the correct API key."""
    c = app.test_client()
    c.environ_base["HTTP_X_API_KEY"] = API_KEY
    return c


@pytest.fixture
def anon(app):
    """Client that sends no credentials."""
    return app.test_client()


def ingest(client, event: dict | str, **kwargs):
    if isinstance(event, str):
        event = SAMPLES[event]
    return client.post("/ingest", json=event, **kwargs)
