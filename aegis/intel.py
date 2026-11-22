"""Threat-intel lookup and enrichment.

`LocalFeedProvider` reads data/intel_feed.json (RFC 5737 documentation
addresses only). `MispProvider` shows how a real MISP instance would plug in;
it is never enabled by default and never called by the tests.
"""

import ipaddress
import json
from pathlib import Path
from typing import Protocol

INTEL_BOOST = 60
MATCH_TAG = "threat.indicator.matched"


class IntelProvider(Protocol):
    def lookup(self, ip: str) -> dict | None: ...


class LocalFeedProvider:
    def __init__(self, feed_path: Path) -> None:
        data = json.loads(Path(feed_path).read_text(encoding="utf-8"))
        self._by_ip = {item["ip"]: item for item in data["indicators"]}

    def lookup(self, ip: str) -> dict | None:
        try:
            key = str(ipaddress.ip_address(ip))
        except ValueError:
            return None
        return self._by_ip.get(key)


class MispProvider:
    """Stub for a MISP REST backend (restSearch on attribute values)."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 5.0) -> None:
        if not api_key:
            raise ValueError("MISP provider needs an API key")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def lookup(self, ip: str) -> dict | None:
        import requests  # imported lazily: only needed when MISP is enabled

        resp = requests.post(
            f"{self.base_url}/attributes/restSearch",
            json={"value": ip, "type": ["ip-src", "ip-dst"], "limit": 1},
            headers={"Authorization": self.api_key, "Accept": "application/json"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        hits = resp.json().get("response", {}).get("Attribute", [])
        if not hits:
            return None
        return {"ip": ip, "label": hits[0].get("comment", "MISP attribute"), "confidence": 80}


def enrich(doc: dict, provider: IntelProvider) -> dict:
    hit = provider.lookup(doc["source"]["ip"])
    if hit:
        doc["tags"].append(MATCH_TAG)
        doc["threat"] = {
            "indicator": {"ip": hit["ip"], "description": hit["label"],
                          "confidence": hit.get("confidence", 50)},
        }
        doc["risk_score"] += INTEL_BOOST
    return doc
