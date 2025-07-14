#!/bin/bash
# Quality check script for Jenkins Build Analyzer

echo "🔍 Running code quality checks..."

# Exit on first error
set -e

echo "📋 Running tests..."
pytest --cov=app --cov-report=term-missing

echo "🎨 Checking code formatting..."
black --check .

echo "📦 Checking import sorting..."
isort --check-only .

echo "🔍 Running linting..."
flake8 app/ tests/

echo "🔒 Running security checks..."
bandit -r app/

echo "📊 Running type checking..."
mypy app/

echo "✅ All checks passed!"
