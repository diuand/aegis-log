"""Functional tests: the service does its job (independent of the seeded bugs)."""

from aegis.intel import MATCH_TAG
from aegis.reports import build_summary
from tests.conftest import SAMPLES, ingest


def test_health(anon):
    r = anon.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_clean_event_is_untouched(client):
    doc = ingest(client, "clean").get_json()["event"]
    assert doc["tags"] == []
    assert doc["risk_score"] == 10
    assert "threat" not in doc


def test_intel_match_changes_the_outcome(client):
    doc = ingest(client, "intel_hit").get_json()["event"]
    assert MATCH_TAG in doc["tags"]
    assert doc["risk_score"] == 70
    assert doc["threat"]["indicator"]["ip"] == "198.51.100.23"


def test_rule_ag001_positive_and_negative(client):
    hit = ingest(client, "ag001_positive").get_json()["event"]
    miss = ingest(client, "ag001_negative").get_json()["event"]
    assert "rule:AG-001" in hit["tags"] and hit["risk_score"] == 35
    assert "rule:AG-001" not in miss["tags"]


def test_rule_ag002_positive_and_negative(client):
    hit = ingest(client, "ag002_positive").get_json()["event"]
    miss = ingest(client, "ag002_negative").get_json()["event"]
    assert "rule:AG-002" in hit["tags"] and hit["risk_score"] == 40
    assert "rule:AG-002" not in miss["tags"]


def test_search_returns_only_that_user(client):
    ingest(client, "clean")
    ingest(client, "ag001_positive")
    body = client.get("/events/search", query_string={"user": "jdoe"}).get_json()
    assert body["count"] == 1
    assert body["events"][0]["user"]["name"] == "jdoe"


def test_report_is_served(client):
    r = client.get("/reports/daily-summary.txt")
    assert r.status_code == 200
    assert r.mimetype == "text/plain"
    assert "aegis-log summary" in r.get_data(as_text=True)


def test_missing_report_is_404(client):
    assert client.get("/reports/weekly-summary.txt").status_code == 404


def test_intel_check(client):
    assert client.get("/intel/check", query_string={"ip": "203.0.113.140"}).get_json()["matched"]
    assert not client.get("/intel/check", query_string={"ip": "192.0.2.44"}).get_json()["matched"]


def test_rules_reload(client):
    body = client.post("/admin/rules/reload").get_json()
    assert body["loaded"] == 2
    assert sorted(body["ids"]) == ["AG-001", "AG-002"]


def test_summary_counts_intel_matches(client):
    docs = [ingest(client, name).get_json()["event"] for name in ("intel_hit", "clean")]
    text = build_summary(docs)
    assert "events: 2" in text
    assert "intel matches: 1" in text


def test_samples_cover_every_rule():
    assert {"ag001_positive", "ag001_negative", "ag002_positive", "ag002_negative"} <= SAMPLES.keys()
