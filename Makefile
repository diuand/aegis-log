# On Windows run make from Git Bash (it needs sh); on Linux/macOS any shell works.
ifeq ($(OS),Windows_NT)
BIN := .venv/Scripts
PY ?= py -3.11
else
BIN := .venv/bin
PY ?= python3
endif
PYTHON := $(BIN)/python

.PHONY: setup hooks run test lint sast audit check report register \
        evidence-red evidence-green evidence-push evidence-gitleaks evidence-hook \
        evidence-enrichment review check-register

setup:
	$(PY) -m venv .venv
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -r requirements.txt -r requirements-dev.txt
	$(PYTHON) scripts/init_env.py

hooks:
	$(PYTHON) -m pre_commit install

run:
	$(PYTHON) -m aegis

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check aegis tests scripts

sast:
	$(PYTHON) -m bandit -q -r aegis

audit:
	$(PYTHON) scripts/audit_deps.py

# lint + tests + security scans (bandit, pip-audit). gitleaks runs in the
# pre-commit hook and in CI.
check: lint test sast audit

report:
	$(PYTHON) scripts/make_report.py

register:
	$(PYTHON) scripts/build_register.py

# Seeded-bug tests with strict xfail switched off, so every open bug shows as
# a real failure. Saved as evidence on the baseline.
evidence-red:
	-AEGIS_SHOW_RED=1 $(PYTHON) -m pytest -q -m seeded_bug --tb=line -rf > docs/evidence/baseline-red.txt
	$(PYTHON) scripts/mask_evidence.py docs/evidence/baseline-red.txt
	@tail -n 1 docs/evidence/baseline-red.txt

evidence-push:
	bash scripts/demo_push_refusal.sh > docs/evidence/push-refused-local.txt 2>&1
	$(PYTHON) scripts/mask_evidence.py docs/evidence/push-refused-local.txt

evidence-gitleaks:
	bash scripts/demo_gitleaks_refusal.sh > docs/evidence/gitleaks-refused.txt 2>&1
	$(PYTHON) scripts/mask_evidence.py docs/evidence/gitleaks-refused.txt

evidence-hook:
	$(PYTHON) scripts/demo_agent_hook.py > docs/evidence/hook-blocked.txt

# The same seeded-bug tests as evidence-red, on main: all must pass.
evidence-green:
	AEGIS_SHOW_RED=1 $(PYTHON) -m pytest -v -m seeded_bug --tb=short > docs/evidence/final-green.txt
	$(PYTHON) scripts/mask_evidence.py docs/evidence/final-green.txt
	@tail -n 1 docs/evidence/final-green.txt

evidence-enrichment:
	$(PYTHON) scripts/demo_enrichment.py > docs/evidence/enrichment.txt

check-register:
	$(PYTHON) scripts/check_register.py

# Mechanical pass of skills/review-pr against main.
review:
	$(PYTHON) skills/review-pr/review.py
