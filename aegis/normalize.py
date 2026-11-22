"""Validate a raw log event and map it to a small ECS-like document."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

BASE_RISK = 10
MAX_BODY_BYTES = 64 * 1024


class RawEvent(BaseModel):
    """The only shape /ingest accepts. Anything else is a 400."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ts: datetime
    src_ip: IPvAnyAddress
    dst_ip: IPvAnyAddress
    user: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._@'\-]+$")
    message: str = Field(min_length=1, max_length=4096)


def normalize(event: RawEvent) -> dict:
    return {
        "@timestamp": event.ts.isoformat(),
        "event": {"kind": "event", "module": "aegis"},
        "source": {"ip": str(event.src_ip)},
        "destination": {"ip": str(event.dst_ip)},
        "user": {"name": event.user},
        "message": event.message,
        "tags": [],
        "risk_score": BASE_RISK,
    }
