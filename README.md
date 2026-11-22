# aegis-log

A small log-enrichment service built for the ULBS Cybersecurity Master,
Module 4 (Risk and Damage Management).

> **This version is deliberately vulnerable.** It carries ten seeded bugs
> (B-01 to B-10, see `tests/bug_ledger.py`). Each one is fixed in its own
> pull request later. Run it only on `127.0.0.1`.

## Run it

```bash
make setup     # .venv + dependencies
make run       # serves on http://127.0.0.1:5000
make check     # lint + tests
```

On Windows, run `make` from Git Bash.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/ingest` | normalize, enrich from the intel feed, apply rules, store |
| GET | `/events/search?user=` | search stored events |
| GET | `/reports/<name>` | serve a text report from `reports/` |
| GET | `/intel/check?ip=` | is this IP in the local intel feed? |
| POST | `/admin/rules/reload` | reload `rules/*.yaml` |

The risk register (`RISK-REGISTER.xlsx`) came first; every change cites its
risk IDs.
