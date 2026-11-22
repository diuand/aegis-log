"""Authentication details beyond the B-06 regression tests."""

import dataclasses

from aegis import create_app
from tests.conftest import API_KEY, ingest


def test_every_endpoint_except_health_requires_the_key(anon):
    assert anon.get("/health").status_code == 200
    for method, path in [("get", "/events/search?user=jdoe"), ("get", "/reports/daily-summary.txt"),
                         ("get", "/intel/check?ip=192.0.2.1"), ("post", "/admin/rules/reload")]:
        assert getattr(anon, method)(path).status_code == 401, path


def test_empty_configured_key_refuses_everyone(settings):
    app = create_app(dataclasses.replace(settings, api_key=""))
    c = app.test_client()
    assert ingest(c, "clean", headers={"X-API-Key": ""}).status_code == 401
    assert c.get("/health").status_code == 200


def test_correct_key_is_accepted(anon):
    assert ingest(anon, "clean", headers={"X-API-Key": API_KEY}).status_code == 201


def test_entry_point_refuses_to_start_without_a_key(monkeypatch, tmp_path):
    from aegis import __main__ as entry

    monkeypatch.setenv("AEGIS_ENV_FILE", str(tmp_path / "none.env"))
    monkeypatch.delenv("AEGIS_API_KEY", raising=False)
    assert entry.main() == 1
