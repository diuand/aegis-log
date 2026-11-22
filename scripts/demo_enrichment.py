#!/usr/bin/env python3
"""Evidence: enrichment changes an outcome (make evidence-enrichment).

Runs the real app in-process against a temporary database and sends the
named samples from samples/events.json. Only the event from a feed IP is
tagged and scored up; the clean event with the same message is untouched.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

KEY = "demo-only-key"


def main() -> None:
    samples = json.loads((ROOT / "samples" / "events.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        os.environ.update({"AEGIS_DB": str(Path(tmp) / "demo.sqlite3"), "AEGIS_API_KEY": KEY,
                           "AEGIS_ENV_FILE": str(Path(tmp) / "none.env")})
        from aegis import create_app

        client = create_app().test_client()
        print("# make evidence-enrichment: same pipeline, different source IPs")
        print(f"{'sample':16} {'src_ip':15} {'risk':>4}  tags")
        for name in ("intel_hit", "clean", "ag001_positive", "ag001_negative",
                     "ag002_positive", "ag002_negative"):
            r = client.post("/ingest", json=samples[name], headers={"X-API-Key": KEY})
            doc = r.get_json()["event"]
            tags = ", ".join(doc["tags"]) or "-"
            print(f"{name:16} {doc['source']['ip']:15} {doc['risk_score']:>4}  {tags}")
            if "threat" in doc:
                print(f"{'':16} threat.indicator: {json.dumps(doc['threat']['indicator'])}")


if __name__ == "__main__":
    main()
