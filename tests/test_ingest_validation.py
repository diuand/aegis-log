"""Malformed input never crashes ingest and never leaks internals (B-05)."""

import json

import pytest

from tests.conftest import ROOT, SAMPLES, ingest

MALFORMED = json.loads((ROOT / "samples" / "malformed.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", MALFORMED, ids=[c["name"] for c in MALFORMED])
def test_malformed_sample_is_a_clean_400(client, case):
    r = client.post("/ingest", json=case["body"])
    assert r.status_code == 400
    assert r.is_json and "error" in r.get_json()


def test_not_json_at_all_is_400(client):
    r = client.post("/ingest", data=b"\xff\xfe not json", content_type="application/json")
    assert r.status_code == 400


def test_validation_error_does_not_echo_the_value(client):
    r = ingest(client, dict(SAMPLES["clean"], user="<script>MARKER</script>"))
    assert r.status_code == 400
    assert "MARKER" not in r.get_data(as_text=True)
    assert r.get_json()["fields"] == ["user"]


def test_unexpected_error_is_a_generic_500(app, client, monkeypatch):
    def boom(_doc):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(app.extensions["aegis"]["store"], "add", boom)
    r = ingest(client, "clean")
    assert r.status_code == 500
    body = r.get_data(as_text=True)
    assert "Traceback" not in body and "secret internal detail" not in body
