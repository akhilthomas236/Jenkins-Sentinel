.PHONY: help install test lint format clean run dev docker

# Default target
help:
	@echo "Jenkins Sentinel - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  install-dev Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run         Run the application"
	@echo "  dev         Run in development mode with reload"
	@echo "  test        Run tests"
	@echo "  test-cov    Run tests with coverage"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code"
	@echo "  check       Run all quality checks"
	@echo ""
	@echo "Database:"
	@echo "  db-init     Initialize database"
	@echo "  db-migrate  Run database migrations"
	@echo "  db-rollback Rollback last migration"
	@echo "  db-cleanup  Clean up old data"
	@echo ""
	@echo "Docker:"
	@echo "  docker      Build and run with Docker"
	@echo "  clean       Clean up build artifacts"

# Installation
install:
	uv pip install -r requirements.txt

install-dev:
	uv pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

# Development
run:
	python -m app.main

dev:
	python -m app.main --reload

test:
	pytest

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term-missing

lint:
	flake8 app/ tests/
	mypy app/
	bandit -r app/

format:
	black .
	isort .

check:
	./scripts/check_all.sh

# Database
db-init:
	python dbmanage.py init

db-migrate:
	python dbmanage.py migrate

db-rollback:
	python dbmanage.py rollback

db-cleanup:
	python dbmanage.py cleanup

# Docker
docker:
	docker build -t jenkins-sentinel .
	docker run -d --name jenkins-sentinel --env-file .env -p 8002:8002 jenkins-sentinel

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
