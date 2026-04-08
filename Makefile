.PHONY: help setup dev dev-prod export-frontend test test-unit test-integration format format-check clean \
	docker-build docker-up docker-logs docker-ps docker-down

APP_NAME := JLPT_generator

OLLAMA_HOST ?= https://ollama.com
OLLAMA_API_KEY ?=
OLLAMA_MODEL ?=

API_URL ?= http://localhost:8000

help:
	@echo "JLPT Generator (Reflex) - common commands"
	@echo ""
	@echo "Local (uv):"
	@echo "  make setup             Install/sync deps into .venv (uv)"
	@echo "  make dev               Run Reflex dev server"
	@echo "  make dev-prod          Run Reflex in prod mode locally"
	@echo "  make test              Run pytest (all)"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make format            Run isort + black"
	@echo "  make format-check      Check formatting without modifying files"
	@echo "  make export-frontend   Export static frontend (set API_URL for deployment)"
	@echo "  make clean             Remove build artifacts"
	@echo ""
	@echo "Docker Compose:"
	@echo "  make docker-build      Build images"
	@echo "  make docker-up         Start services in background"
	@echo "  make docker-ps         Show service status"
	@echo "  make docker-logs       Tail recent logs"
	@echo "  make docker-down       Stop services"

setup:
	uv sync

dev:
	OLLAMA_HOST="$(OLLAMA_HOST)" OLLAMA_API_KEY="$(OLLAMA_API_KEY)" OLLAMA_MODEL="$(OLLAMA_MODEL)" uv run reflex run

dev-prod:
	OLLAMA_HOST="$(OLLAMA_HOST)" OLLAMA_API_KEY="$(OLLAMA_API_KEY)" OLLAMA_MODEL="$(OLLAMA_MODEL)" uv run reflex run --env prod

test:
	uv run pytest

test-unit:
	uv run pytest -m unit

test-integration:
	uv run pytest -m integration

format:
	uv run isort .
	uv run black .

format-check:
	uv run isort . --check-only
	uv run black . --check

export-frontend:
	API_URL="$(API_URL)" uv run reflex export --frontend-only --no-zip
	@echo ""
	@echo "Exported static frontend to: .web/build/client/"

clean:
	rm -rf .web/build .pytest_cache .ruff_cache .mypy_cache **/__pycache__

docker-build:
	docker compose build

docker-up:
	OLLAMA_API_KEY=$(OLLAMA_API_KEY) docker compose up -d

docker-ps:
	docker compose ps

docker-logs:
	docker compose logs --no-color --tail=200

docker-down:
	docker compose down -v

