"""Map a raw log event to a small ECS-like document."""

BASE_RISK = 10


def normalize(raw: dict) -> dict:
    return {
        "@timestamp": raw["ts"],
        "event": {"kind": "event", "module": "aegis"},
        "source": {"ip": raw["src_ip"]},
        "destination": {"ip": raw["dst_ip"]},
        "user": {"name": raw["user"]},
        "message": raw["message"],
        "tags": [],
        "risk_score": BASE_RISK,
    }
