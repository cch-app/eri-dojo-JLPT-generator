.PHONY: help setup dev dev-prod test test-unit test-integration format format-check clean \
	docker-build docker-up docker-logs docker-ps docker-down

APP_NAME := JLPT_generator

OLLAMA_HOST ?= https://ollama.com
OLLAMA_API_KEY ?=
OLLAMA_MODEL ?=

FLASK_HOST ?= 127.0.0.1
FLASK_PORT ?= 8000

help:
	@echo "JLPT Generator (Flask) - common commands"
	@echo ""
	@echo "Local (uv):"
	@echo "  make setup             Install/sync deps into .venv (uv)"
	@echo "  make dev               Run Flask dev server"
	@echo "  make dev-prod          Run gunicorn locally (prod-ish)"
	@echo "  make test              Run pytest (all)"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make format            Run isort + black"
	@echo "  make format-check      Check formatting without modifying files"
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
	OLLAMA_HOST="$(OLLAMA_HOST)" OLLAMA_API_KEY="$(OLLAMA_API_KEY)" OLLAMA_MODEL="$(OLLAMA_MODEL)" \
	FLASK_APP="api.wsgi:app" FLASK_ENV=development \
	uv run flask run --host "$(FLASK_HOST)" --port "$(FLASK_PORT)"

dev-prod:
	OLLAMA_HOST="$(OLLAMA_HOST)" OLLAMA_API_KEY="$(OLLAMA_API_KEY)" OLLAMA_MODEL="$(OLLAMA_MODEL)" \
	uv run gunicorn -w 2 -b 0.0.0.0:8000 api.wsgi:app

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

