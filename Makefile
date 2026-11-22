# On Windows run make from Git Bash (it needs sh); on Linux/macOS any shell works.
ifeq ($(OS),Windows_NT)
BIN := .venv/Scripts
PY ?= py -3.11
else
BIN := .venv/bin
PY ?= python3
endif
PYTHON := $(BIN)/python

.PHONY: setup run test lint check report register evidence-red

setup:
	$(PY) -m venv .venv
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -r requirements.txt -r requirements-dev.txt

run:
	$(PYTHON) -m aegis

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check aegis tests scripts

check: lint test

report:
	$(PYTHON) scripts/make_report.py

register:
	$(PYTHON) scripts/build_register.py

# Runs the seeded-bug tests with strict xfail switched off, so every open bug
# shows as a real failure. Saved as evidence on the baseline.
evidence-red:
	-AEGIS_SHOW_RED=1 $(PYTHON) -m pytest -q -m seeded_bug --tb=line -rf > docs/evidence/baseline-red.txt
	$(PYTHON) scripts/mask_evidence.py docs/evidence/baseline-red.txt
	@tail -n 1 docs/evidence/baseline-red.txt
