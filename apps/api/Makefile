VENV := .venv

# ---------------------------------------------------------------------------
# Detecção de sistema
# No Windows forçamos o cmd.exe como shell, para o comportamento ser o mesmo
# rodando o make pelo PowerShell, cmd ou Git Bash.
# ---------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
  SHELL := cmd.exe
  .SHELLFLAGS := /c
  PYTHON ?= python
  PY := $(VENV)\Scripts\python.exe
  ACTIVATE := .\$(VENV)\Scripts\Activate.ps1
else
  PYTHON ?= python3
  PY := $(VENV)/bin/python
  ACTIVATE := source $(VENV)/bin/activate
endif

PIP := $(PY) -m pip
HOST ?= 0.0.0.0
PORT ?= 8000
export PYTHONPATH := src

.DEFAULT_GOAL := help
.PHONY: help setup venv install install-dev run dev-test test lint fmt check clean

help:
	@echo Targets:
	@echo   make setup        cria venv + instala deps (prod + dev)
	@echo   make run          roda a API com reload (HOST=$(HOST) PORT=$(PORT))
	@echo   make dev-test     sobe a API, testa /health e derruba
	@echo   make test         roda os testes (pytest)
	@echo   make lint         ruff check
	@echo   make fmt          ruff format
	@echo   make check        lint + test
	@echo   make clean        remove caches/artefatos (mantem a venv)

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt

setup: venv install install-dev
	@echo Setup concluido. Ative a venv com: $(ACTIVATE)

run:
	$(PY) -m uvicorn app.main:app --reload --host $(HOST) --port $(PORT)

dev-test:
	$(PY) scripts/dev_test.py

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .

fmt:
	$(PY) -m ruff format .

check: lint test

clean:
	$(PY) -c "import pathlib, shutil; root = pathlib.Path('.'); dirs = [root / '.pytest_cache', root / '.ruff_cache', *root.rglob('__pycache__')]; [shutil.rmtree(d, ignore_errors=True) for d in dirs if '.venv' not in d.parts]; [f.unlink() for f in root.rglob('*.pyc') if '.venv' not in f.parts and f.exists()]"
