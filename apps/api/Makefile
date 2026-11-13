VENV := .venv

# ---------------------------------------------------------------------------
# Detecção de sistema
# No Windows forçamos o cmd.exe como shell, para o comportamento ser o mesmo
# rodando o make pelo PowerShell, cmd ou Git Bash.
# PYTHON escolhe o interpretador que cria a venv (3.12, ver .python-version);
# dá para trocar: make setup PYTHON=...
# ---------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
  SHELL := cmd.exe
  .SHELLFLAGS := /c
  ifneq ($(shell where py 2>NUL),)
    PYTHON ?= py -3.12
  else
    PYTHON ?= python
  endif
  PY := $(VENV)\Scripts\python.exe
  VENV_PY := $(VENV)/Scripts/python.exe
  ACTIVATE := .\$(VENV)\Scripts\Activate.ps1
  COPY_ENV := if not exist .env copy .env.example .env >NUL && echo .env criado a partir do .env.example
else
  ifneq ($(shell command -v python3.12),)
    PYTHON ?= python3.12
  else
    PYTHON ?= python3
  endif
  PY := $(VENV)/bin/python
  VENV_PY := $(VENV)/bin/python
  ACTIVATE := source $(VENV)/bin/activate
  COPY_ENV := [ -f .env ] || { cp .env.example .env && echo .env criado a partir do .env.example; }
endif

PIP := $(PY) -m pip
# Marca de "dependências instaladas": refeita só quando os requirements mudam.
DEPS_OK := $(VENV)/.deps-ok
HOST ?= 0.0.0.0
PORT ?= 8000
export PYTHONPATH := src

.DEFAULT_GOAL := help
.PHONY: help setup venv install install-dev env run dev-test test lint fmt check clean

help:
	@echo Targets:
	@echo   make setup        cria a venv, instala deps prod + dev e cria o .env se faltar
	@echo   make run          roda a API com reload - HOST=$(HOST) PORT=$(PORT)
	@echo   make dev-test     sobe a API na PORT, testa /health e derruba
	@echo   make test         roda os testes - pytest
	@echo   make lint         ruff check
	@echo   make fmt          ruff format
	@echo   make check        lint + test
	@echo   make install      reinstala as deps na venv existente
	@echo   make clean        remove caches/artefatos - mantem a venv

# A venv só é criada se ainda não existir.
$(VENV_PY):
	$(PYTHON) -m venv $(VENV)

venv: $(VENV_PY)

$(DEPS_OK): $(VENV_PY) requirements.txt requirements-dev.txt
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	$(PY) -c "open('$(DEPS_OK)', 'w').close()"

install: $(VENV_PY)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PY) -c "import pathlib; pathlib.Path('$(DEPS_OK)').unlink(missing_ok=True)"

install-dev: $(VENV_PY)
	$(PIP) install -r requirements-dev.txt
	$(PY) -c "import pathlib; pathlib.Path('$(DEPS_OK)').unlink(missing_ok=True)"

env:
	@$(COPY_ENV)

setup: $(DEPS_OK) env
	@echo Setup concluido. Ative a venv com: $(ACTIVATE)

run: $(DEPS_OK)
	$(PY) -m uvicorn app.main:app --reload --host $(HOST) --port $(PORT)

dev-test: $(DEPS_OK)
	$(PY) scripts/dev_test.py $(PORT)

test: $(DEPS_OK)
	$(PY) -m pytest

lint: $(DEPS_OK)
	$(PY) -m ruff check .

fmt: $(DEPS_OK)
	$(PY) -m ruff format .

check: lint test

# Usa o PYTHON do sistema: funciona mesmo sem a venv.
clean:
	$(PYTHON) -c "import pathlib, shutil; root = pathlib.Path('.'); dirs = [root / '.pytest_cache', root / '.ruff_cache', *root.rglob('__pycache__')]; [shutil.rmtree(d, ignore_errors=True) for d in dirs if '.venv' not in d.parts]; [f.unlink() for f in root.rglob('*.pyc') if '.venv' not in f.parts and f.exists()]"
