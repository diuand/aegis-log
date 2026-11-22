"""Regression tests for the ten seeded bugs.

Every test exercises the real exploit path with a harmless marker. While a bug
is listed in tests/bug_ledger.py these tests are strict xfail (they must fail);
`make evidence-red` runs them as plain tests to show the failures.
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest
import yaml

from aegis.config import load_settings
from aegis.rules import load_rules
from tests import yaml_canary
from tests.conftest import API_KEY, ROOT, SAMPLES, ingest

seeded = pytest.mark.seeded_bug


# ---------------------------------------------------------------- B-01
@seeded("B-01")
def test_b01_no_credential_literal_in_source():
    key_shape = re.compile(r"aegk_[A-Za-z0-9]{20,}")
    offenders = [str(p.relative_to(ROOT)) for p in (ROOT / "aegis").rglob("*.py")
                 if key_shape.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


@seeded("B-01")
def test_b01_intel_key_comes_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_ENV_FILE", str(tmp_path / "none.env"))
    monkeypatch.setenv("AEGIS_INTEL_API_KEY", "from-environment-marker")
    assert load_settings().intel_api_key == "from-environment-marker"


@seeded("B-01")
def test_b01_intel_key_is_empty_when_not_configured(monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_ENV_FILE", str(tmp_path / "none.env"))
    monkeypatch.delenv("AEGIS_INTEL_API_KEY", raising=False)
    assert load_settings().intel_api_key == ""


# ---------------------------------------------------------------- B-02
def _two_users(client):
    ingest(client, "clean")  # jdoe
    ingest(client, "ag001_positive")  # oracle


@seeded("B-02")
def test_b02_tautology_does_not_dump_every_event(client):
    _two_users(client)
    r = client.get("/events/search", query_string={"user": "x' OR '1'='1"})
    assert r.status_code == 200
    assert r.get_json()["count"] == 0


@seeded("B-02")
def test_b02_quote_in_a_name_is_treated_as_data(client):
    ingest(client, dict(SAMPLES["clean"], user="o'neil"))
    r = client.get("/events/search", query_string={"user": "o'neil"})
    assert r.status_code == 200
    assert r.get_json()["count"] == 1


@seeded("B-02")
def test_b02_union_cannot_read_outside_the_events_table(settings):
    from aegis.store import EventStore

    store = EventStore(settings.db_path)
    assert store.search_by_user("' UNION SELECT json_quote(sqlite_version()) --") == []


# ---------------------------------------------------------------- B-03
MARKER = "AEGIS-TRAVERSAL-MARKER"


@seeded("B-03")
def test_b03_dotdot_cannot_leave_reports_dir(client, workdir):
    (workdir / "secret.txt").write_text(MARKER, encoding="utf-8")
    r = client.get("/reports/..%2Fsecret.txt")
    assert r.status_code == 404
    assert MARKER not in r.get_data(as_text=True)


@seeded("B-03")
def test_b03_absolute_path_cannot_be_requested(client, workdir):
    secret = workdir / "secret.txt"
    secret.write_text(MARKER, encoding="utf-8")
    r = client.get("/reports/" + quote(str(secret), safe=""))
    assert r.status_code == 404
    assert MARKER not in r.get_data(as_text=True)


@seeded("B-03")
def test_b03_only_allowlisted_report_names_are_served(client, workdir):
    (workdir / "reports" / "notes.md").write_text(MARKER, encoding="utf-8")
    assert client.get("/reports/notes.md").status_code == 404


# ---------------------------------------------------------------- B-04
@seeded("B-04")
def test_b04_python_tags_in_rules_do_not_execute(tmp_path):
    yaml_canary.TRIPPED.clear()
    (tmp_path / "evil.yaml").write_text(
        "id: AG-666\ntitle: canary\nseverity: low\nrisk: 1\n"
        "when: !!python/object/apply:tests.yaml_canary.trip [AEGIS-YAML-MARKER]\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_rules(tmp_path)
    assert yaml_canary.TRIPPED == []


@seeded("B-04")
def test_b04_reload_rejects_a_broken_rule_and_keeps_the_old_set(client, workdir):
    (workdir / "rules" / "zz-broken.yaml").write_text(
        "id: AG-900\ntitle: missing conditions\nseverity: low\nrisk: 5\n", encoding="utf-8")
    r = client.post("/admin/rules/reload")
    assert r.status_code == 400
    doc = ingest(client, "ag001_positive").get_json()["event"]
    assert "rule:AG-001" in doc["tags"]


@seeded("B-04")
def test_b04_duplicate_rule_ids_are_rejected(tmp_path):
    for name in ("a.yaml", "b.yaml"):
        (tmp_path / name).write_text(
            "id: AG-001\ntitle: dup\nseverity: low\nrisk: 5\nwhen:\n  message:\n    contains: x\n",
            encoding="utf-8")
    with pytest.raises(ValueError):
        load_rules(tmp_path)


# ---------------------------------------------------------------- B-05
@seeded("B-05")
def test_b05_missing_field_is_400_not_500(client):
    event = dict(SAMPLES["clean"])
    del event["src_ip"]
    r = ingest(client, event)
    assert r.status_code == 400
    assert "src_ip" in r.get_data(as_text=True)


@seeded("B-05")
def test_b05_json_array_is_400_not_500(client):
    assert client.post("/ingest", json=[SAMPLES["clean"]]).status_code == 400


@seeded("B-05")
def test_b05_invalid_ip_is_rejected(client):
    assert ingest(client, dict(SAMPLES["clean"], src_ip="not-an-ip")).status_code == 400


@seeded("B-05")
def test_b05_oversized_body_is_413(client):
    big = dict(SAMPLES["clean"], message="A" * (70 * 1024))
    assert ingest(client, big).status_code == 413


# ---------------------------------------------------------------- B-06
@seeded("B-06")
def test_b06_ingest_requires_an_api_key(anon):
    assert ingest(anon, "clean").status_code == 401


@seeded("B-06")
def test_b06_admin_reload_requires_an_api_key(anon):
    assert anon.post("/admin/rules/reload").status_code == 401


@seeded("B-06")
def test_b06_wrong_api_key_is_rejected(anon):
    r = ingest(anon, "clean", headers={"X-API-Key": API_KEY[:-1] + "x"})
    assert r.status_code == 401


@seeded("B-06")
def test_b06_entry_point_never_enables_debug():
    tree = ast.parse((ROOT / "aegis" / "__main__.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "run":
            for kw in node.keywords:
                if kw.arg == "debug":
                    assert isinstance(kw.value, ast.Constant) and kw.value.value is False


# ---------------------------------------------------------------- B-07
@seeded("B-07")
def test_b07_credentials_in_headers_never_reach_the_log(client, caplog):
    caplog.set_level("INFO")
    ingest(client, "clean", headers={"Authorization": "Bearer AEGIS-TOKEN-MARKER"})
    assert "AEGIS-TOKEN-MARKER" not in caplog.text
    assert API_KEY not in caplog.text


@seeded("B-07")
def test_b07_newline_cannot_forge_a_log_line(client, caplog):
    caplog.set_level("INFO")
    forged = "vpn ok\n2026-11-20 09:00:00 INFO aegis admin access granted"
    ingest(client, dict(SAMPLES["clean"], message=forged))
    assert caplog.records
    assert all("\n" not in rec.getMessage() for rec in caplog.records)


@seeded("B-07")
def test_b07_password_in_message_is_redacted(client, caplog):
    caplog.set_level("INFO")
    ingest(client, dict(SAMPLES["clean"], message="login failed password=Hunter2Marker"))
    assert "Hunter2Marker" not in caplog.text


# ---------------------------------------------------------------- B-08
def _requirements() -> list[str]:
    lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return [ln.split("#")[0].strip() for ln in lines if ln.split("#")[0].strip()]


@seeded("B-08")
def test_b08_every_runtime_dependency_is_pinned_exactly():
    unpinned = [r for r in _requirements() if not re.fullmatch(r"[A-Za-z0-9_.\-\[\]]+==[0-9][\w.]*", r)]
    assert unpinned == []


@seeded("B-08")
def test_b08_requests_is_past_the_known_cves():
    pins = dict(r.split("==") for r in _requirements() if "==" in r)
    version = tuple(int(x) for x in pins.get("requests", "0").split(".")[:3])
    assert version >= (2, 32, 4)  # CVE-2024-35195 fixed in 2.32.0, CVE-2024-47081 in 2.32.4


# ---------------------------------------------------------------- B-09
def _workflows() -> dict[str, dict]:
    files = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
    return {p.name: yaml.safe_load(p.read_text(encoding="utf-8")) for p in files}


def _triggers(wf: dict) -> dict:
    # PyYAML (YAML 1.1) reads the bare key `on` as boolean True.
    trig = wf.get("on", wf.get(True, {}))
    return trig if isinstance(trig, dict) else {t: None for t in ([trig] if isinstance(trig, str) else trig)}


@seeded("B-09")
def test_b09_no_workflow_uses_pull_request_target():
    flows = _workflows()
    assert "ci-baseline.yml" not in flows
    assert flows, "expected at least one workflow"
    assert [n for n, wf in flows.items() if "pull_request_target" in _triggers(wf)] == []


@seeded("B-09")
def test_b09_workflow_tokens_are_least_privilege():
    for name, wf in _workflows().items():
        perms = wf.get("permissions")
        assert isinstance(perms, dict), f"{name}: top-level permissions must be an explicit map"
        assert perms.get("contents") == "read", name
        assert "write-all" not in json.dumps(wf), name


@seeded("B-09")
def test_b09_every_action_is_pinned_to_a_full_sha():
    unpinned = []
    for name, wf in _workflows().items():
        for job in wf.get("jobs", {}).values():
            for step in job.get("steps", []):
                uses = step.get("uses")
                if uses and not uses.startswith("./") and not re.search(r"@[0-9a-f]{40}$", uses):
                    unpinned.append(f"{name}: {uses}")
    assert unpinned == []


# ---------------------------------------------------------------- B-10
POISON = re.compile(r"push (straight|directly) to main|skip (the )?tests|--no-verify", re.I)


@seeded("B-10")
def test_b10_no_memory_note_tells_the_agent_to_bypass_controls():
    notes = [*(ROOT / ".claude").rglob("*.md"), *(ROOT / "memory").rglob("*.md"), ROOT / "CLAUDE.md"]
    bad = [str(p.relative_to(ROOT)) for p in notes
           if p.is_file() and POISON.search(p.read_text(encoding="utf-8"))
           and "aegis:quarantined" not in p.read_text(encoding="utf-8")]
    assert bad == []


@seeded("B-10")
def test_b10_agent_settings_deny_dangerous_actions():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    deny = " ".join(settings["permissions"]["deny"])
    for needle in ("git push origin main", "--force", ".env"):
        assert needle in deny, needle
    assert settings["hooks"]["PreToolUse"], "PreToolUse hook must be configured"


def _guard(command: str) -> int:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    proc = subprocess.run([sys.executable, str(ROOT / ".claude" / "hooks" / "guard.py")],
                          input=payload, capture_output=True, text=True, timeout=20)
    return proc.returncode


@seeded("B-10")
def test_b10_guard_hook_blocks_push_to_main():
    assert (ROOT / ".claude" / "hooks" / "guard.py").is_file()
    assert _guard("git push origin main") == 2
    assert _guard("git push --force origin fix/b-01") == 2


@seeded("B-10")
def test_b10_guard_hook_allows_ordinary_work():
    assert (ROOT / ".claude" / "hooks" / "guard.py").is_file()
    assert _guard("git status") == 0
    assert _guard("git push -u origin fix/b-02-sql-injection") == 0


def test_seeded_ids_match_the_ledger():
    """Every ID in the ledger must still have tests (no ID can be dropped quietly)."""
    from tests.bug_ledger import OPEN_BUGS

    text = Path(__file__).read_text(encoding="utf-8")
    assert all(f'@seeded("{bug}")' in text for bug in OPEN_BUGS)
