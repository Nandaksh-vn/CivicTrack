# =============================================================================
# CivicTrack Makefile - developer shortcuts
# Requires: make, docker compose, Python 3.12+, Node 20+ / npm
# =============================================================================

PYTHON  ?= python
NPM     ?= npm
COMPOSE ?= docker compose
BACKEND := backend
FRONTEND := frontend

.PHONY: help install install-backend install-frontend \
        dev dev-api dev-web \
        lint lint-backend lint-frontend \
        typecheck typecheck-backend typecheck-frontend \
        test test-backend test-frontend test-e2e \
        format migrate seed \
        compose-up compose-down compose-down-volumes compose-logs compose-ps \
        compose-config compose-restart \
        build build-frontend \
        pre-commit-install pre-commit-run clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'

# -- Install ------------------------------------------------------------------
install: install-backend install-frontend  ## Install all dependencies

install-backend:  ## Install Python dependencies
	cd $(BACKEND) && $(PYTHON) -m pip install -e ".[dev]"

install-frontend:  ## Install Node dependencies from the lockfile
	cd $(FRONTEND) && $(NPM) ci

# -- Dev servers --------------------------------------------------------------
dev: compose-up  ## Start the full stack via docker compose

dev-api:  ## Start the FastAPI dev server locally
	cd $(BACKEND) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:  ## Start the Vite dev server locally
	cd $(FRONTEND) && $(NPM) run dev

# -- Lint ---------------------------------------------------------------------
lint: lint-backend lint-frontend  ## Lint all code

lint-backend:  ## Run ruff linter and formatter check
	cd $(BACKEND) && ruff check . && ruff format --check .

lint-frontend:  ## Run ESLint
	cd $(FRONTEND) && $(NPM) run lint

# -- Typecheck ----------------------------------------------------------------
typecheck: typecheck-backend typecheck-frontend  ## Typecheck all code

typecheck-backend:  ## Run mypy
	cd $(BACKEND) && mypy app

typecheck-frontend:  ## Run tsc --noEmit
	cd $(FRONTEND) && $(NPM) run typecheck

# -- Tests --------------------------------------------------------------------
test: test-backend test-frontend  ## Run backend and frontend tests

test-backend:  ## Run pytest with coverage
	cd $(BACKEND) && pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend:  ## Run Vitest once
	cd $(FRONTEND) && $(NPM) run test:run

test-e2e:  ## Run Playwright e2e tests (needs a running web server)
	cd $(FRONTEND) && $(NPM) run e2e

# -- Formatting ---------------------------------------------------------------
format:  ## Format backend and frontend code
	cd $(BACKEND) && ruff check --fix . && ruff format .
	cd $(FRONTEND) && $(NPM) run format

# -- Database -----------------------------------------------------------------
migrate:  ## Run alembic upgrade head
	cd $(BACKEND) && alembic upgrade head

migrate-down:  ## Roll back the last migration
	cd $(BACKEND) && alembic downgrade -1

seed:  ## Seed demo data (idempotent; Phase 19 dataset)
	cd $(BACKEND) && $(PYTHON) -m app.seed

seed-check:  ## Verify the demo dataset incl. the overdue candidate
	cd $(BACKEND) && $(PYTHON) -m app.seed --check

# -- Docker Compose -----------------------------------------------------------
compose-up:  ## Build and start all services in the background
	$(COMPOSE) up -d --build

compose-down:  ## Stop containers, keep volumes
	$(COMPOSE) down

compose-down-volumes:  ## Stop containers and delete volumes (destructive!)
	$(COMPOSE) down -v

compose-logs:  ## Follow logs from all services
	$(COMPOSE) logs -f

compose-ps:  ## Show container status
	$(COMPOSE) ps

compose-config:  ## Validate the Compose file without starting containers
	$(COMPOSE) config

compose-restart:  ## Restart all services
	$(COMPOSE) restart

prod-up:  ## Production stack via the prod overlay (needs production .env)
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-proxy:  ## Production stack + optional Caddy reverse proxy
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml --profile proxy up -d --build

backup:  ## Back up DB + uploads to ./backups
	./scripts/backup.sh ./backups

# -- Build --------------------------------------------------------------------
build: build-frontend  ## Build production frontend assets

build-frontend:  ## Build the React app
	cd $(FRONTEND) && $(NPM) run build

# -- Pre-commit ---------------------------------------------------------------
pre-commit-install:  ## Install git hooks
	pre-commit install

pre-commit-run:  ## Run all hooks against all files
	pre-commit run --all-files

# -- Clean --------------------------------------------------------------------
clean:  ## Remove caches and build artifacts
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('$(BACKEND)').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['$(BACKEND)/.ruff_cache', '$(BACKEND)/.mypy_cache', '$(BACKEND)/.pytest_cache', '$(FRONTEND)/dist', '$(FRONTEND)/node_modules/.vite']]"
