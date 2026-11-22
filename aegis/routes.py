"""HTTP endpoints."""

import hmac
import logging

from flask import Blueprint, Response, abort, current_app, jsonify, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from aegis.intel import enrich
from aegis.logsafe import clean
from aegis.normalize import RawEvent, normalize
from aegis.reports import resolve_report
from aegis.rules import RuleError, apply_rules, load_rules

bp = Blueprint("aegis", __name__)
log = logging.getLogger("aegis")


def _svc(name: str):
    return current_app.extensions["aegis"][name]


OPEN_ENDPOINTS = {"aegis.health"}


@bp.before_app_request
def require_api_key():
    """Deny by default: every endpoint except /health needs the API key."""
    if request.endpoint in OPEN_ENDPOINTS:
        return None
    expected = _svc("settings").api_key.encode()
    supplied = request.headers.get("X-API-Key", "").encode()
    # compare_digest takes the same time whether the first or last byte differs.
    if not expected or not hmac.compare_digest(supplied, expected):
        return jsonify(error="missing or invalid API key"), 401
    return None


@bp.app_errorhandler(HTTPException)
def http_error(exc: HTTPException):
    # JSON errors with the status name only (413, 404, 405, 400 ...).
    return jsonify(error=exc.name), exc.code


@bp.app_errorhandler(Exception)
def unexpected_error(exc: Exception):
    log.error("unhandled error: %s", exc.__class__.__name__)
    return jsonify(error="internal error"), 500


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.post("/ingest")
def ingest():
    raw = request.get_json(silent=True)
    if not isinstance(raw, dict):
        return jsonify(error="body must be a JSON object"), 400
    try:
        event = RawEvent.model_validate(raw)
    except ValidationError as exc:
        # Field names only: never echo the submitted values back.
        fields = sorted({".".join(map(str, e["loc"])) or "<root>" for e in exc.errors()})
        return jsonify(error="invalid event", fields=fields), 400
    # Never log request headers (API keys, cookies); untrusted values go through clean().
    log.info("ingest src=%s user=%s message=%s",
             clean(event.src_ip), clean(event.user), clean(event.message))
    doc = normalize(event)
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
    try:
        rules = load_rules(_svc("settings").rules_dir)
    except RuleError as exc:
        # All or nothing: the previous rule set stays active.
        return jsonify(error="rule set rejected, previous rules kept", detail=str(exc)), 400
    current_app.extensions["aegis"]["rules"] = rules
    return jsonify(loaded=len(rules), ids=[r.id for r in rules])
