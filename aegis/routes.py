"""HTTP endpoints."""

import logging

from flask import Blueprint, Response, abort, current_app, jsonify, request

from aegis.intel import enrich
from aegis.normalize import normalize
from aegis.reports import resolve_report
from aegis.rules import apply_rules, load_rules

bp = Blueprint("aegis", __name__)
log = logging.getLogger("aegis")


def _svc(name: str):
    return current_app.extensions["aegis"][name]


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.post("/ingest")
def ingest():
    raw = request.get_json(force=True)
    log.info("ingest headers=%s message=%s", dict(request.headers), raw.get("message"))
    doc = normalize(raw)
    enrich(doc, _svc("intel"))
    apply_rules(_svc("rules"), doc)
    event_id = _svc("store").add(doc)
    return jsonify(id=event_id, event=doc), 201


@bp.get("/events/search")
def search():
    user = request.args.get("user", "")
    results = _svc("store").search_by_user(user)
    return jsonify(count=len(results), events=results)


@bp.get("/reports/<name>")  # plain converter: no slashes in the name
def report(name: str):
    path = resolve_report(_svc("settings").reports_dir, name)
    if path is None:
        abort(404)
    return Response(path.read_text(encoding="utf-8"), mimetype="text/plain")


@bp.get("/intel/check")
def intel_check():
    ip = request.args.get("ip", "")
    hit = _svc("intel").lookup(ip)
    return jsonify(ip=ip, matched=hit is not None, indicator=hit)


@bp.post("/admin/rules/reload")
def reload_rules():
    rules = load_rules(_svc("settings").rules_dir)
    current_app.extensions["aegis"]["rules"] = rules
    return jsonify(loaded=len(rules), ids=[r.get("id") for r in rules])
