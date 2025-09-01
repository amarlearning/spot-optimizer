.PHONY: clean test coverage lint format install build publish help

# Variables
PYTHON = poetry run python
PYTEST = poetry run pytest
COVERAGE_THRESHOLD = 94
PACKAGE_NAME = spot_optimizer

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies using poetry
	poetry install

clean:  ## Remove all build, test, and coverage artifacts
	rm -rf .venv-*/
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:  ## Run unit tests
	$(PYTEST) tests/ -m "not integration" -v

test-unit:  ## Run unit tests (alias for test)
	$(PYTEST) tests/ -m "not integration" -v

coverage:  ## Run tests with coverage report
	$(PYTEST) tests/ -m "not integration" \
		--cov=$(PACKAGE_NAME) \
		--cov-fail-under=$(COVERAGE_THRESHOLD)

test-with-coverage:  ## Run all tests with coverage
	$(PYTEST) tests/ \
		--cov=$(PACKAGE_NAME) \
		--cov-fail-under=$(COVERAGE_THRESHOLD)

test-integration:  ## Run integration tests
	$(PYTHON) tests/test_integration.py

test-integration-verbose:  ## Run integration tests with verbose output
	CI=true $(PYTHON) tests/test_integration.py

test-all: test test-integration  ## Run all tests (unit + integration)

test-performance:  ## Run performance-focused integration tests
	$(PYTEST) tests/test_integration.py -m performance -v

test-ci: test coverage test-integration  ## Run all tests suitable for CI

test-quick:  ## Run quick test suite (unit tests only)
	$(PYTEST) tests/ -m "not integration" -x --tb=short

test-parallel:  ## Run unit tests in parallel
	$(PYTEST) tests/ -m "not integration" -n auto

test-security:  ## Run security scans
	$(PYTHON) -m safety check --json || true
	$(PYTHON) -m bandit -r $(PACKAGE_NAME)/ -f json || true

test-markers:  ## Show available test markers
	$(PYTEST) --markers

build: clean coverage  ## Build package
	poetry build

publish: build  ## Publish package to PyPI
	python scripts/generate_instance_metadata.py
	poetry publish 
