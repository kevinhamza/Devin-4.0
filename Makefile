# Makefile for the Devin AGI Project

VENV_DIR ?= venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
NPM ?= npm

# Default: `make` (no target) prints help.
.DEFAULT_GOAL := help

help:
	@echo "Devin AGI 4.0 — Makefile targets"
	@echo ""
	@echo "  make setup            Full cold-clone install: venv + pip (locked) + npm + TS build"
	@echo "  make install          Python venv + pinned requirements only"
	@echo "  make install-loose    Python venv + loose requirements.txt (may resolve fresh)"
	@echo "  make ts-build         npm install + npm run build (TypeScript CLI)"
	@echo "  make run              Start Devin (interactive Python REPL)"
	@echo "  make ARGS='...' run-oneshot   One-shot Python invocation"
	@echo "  make devin            Alias for './devin' — prefers dist/cli.js, falls back to Python"
	@echo "  make test             Run pytest suite (excludes performance)"
	@echo "  make test-all         Run pytest including performance benchmarks"
	@echo "  make lint             Fast static checks (Python compile + tsc --noEmit)"
	@echo "  make smoke            main.py --test (verifies imports + tools without an LLM call)"
	@echo "  make benchmark        Run performance benchmarks"
	@echo "  make clean            Remove __pycache__, *.pyc"
	@echo "  make distclean        clean + rm venv/ dist/ node_modules/"

# --- Environment setup ------------------------------------------------------
venv:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment in $(VENV_DIR)..."; \
		python3 -m venv $(VENV_DIR); \
	fi

install: venv
	@echo "Installing pinned dependencies from requirements.lock..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.lock
	@echo ""
	@echo "Python deps installed. Configure .env (cp .env.example .env), then 'make run'."

install-loose: venv
	@echo "Installing loose dependencies from requirements.txt..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

ts-build:
	@echo "Installing Node deps (--legacy-peer-deps handles the eslint 9 vs @typescript-eslint 7 conflict)..."
	$(NPM) install --legacy-peer-deps --no-audit --no-fund
	@echo "Building TypeScript..."
	$(NPM) run build

setup: install ts-build
	@if [ ! -f .env ]; then cp .env.example .env; echo ""; echo "Wrote .env — edit it and add HF_TOKEN or another provider key."; fi
	@echo ""
	@echo "Setup complete. Try: make smoke   then   ./devin"

# --- Running ---------------------------------------------------------------
run:
	@$(PYTHON) main.py

run-oneshot:
	@if [ -z "$(ARGS)" ]; then echo "Usage: make ARGS='your prompt here' run-oneshot"; exit 1; fi
	@$(PYTHON) main.py "$(ARGS)"

devin:
	@./devin

smoke:
	@$(PYTHON) main.py --test

# --- Testing ---------------------------------------------------------------
test:
	@$(PYTHON) -m pytest tests/ --ignore=tests/performance -q --disable-warnings

test-all:
	@$(PYTHON) -m pytest tests/ -q --disable-warnings

benchmark:
	@$(PYTHON) tests/performance/benchmark_ai.py

pentest:
	@$(PYTHON) tests/pentesting/test_self_pentest.py

# --- Linting ---------------------------------------------------------------
lint:
	@echo "== Python compile-check =="
	@$(PYTHON) -m compileall -q main.py modules/ tests/ || true
	@echo "== TypeScript type-check (no emit) =="
	@if [ -d node_modules ]; then \
		$(NPM) exec -- tsc --noEmit; \
	else \
		echo "  (skipped — node_modules missing; run 'make ts-build' first)"; \
	fi

# --- Cleanup ---------------------------------------------------------------
clean:
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true

distclean: clean
	@rm -rf $(VENV_DIR) dist node_modules

.PHONY: help venv install install-loose ts-build setup run run-oneshot devin smoke test test-all benchmark pentest lint clean distclean
