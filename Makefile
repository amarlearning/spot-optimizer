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

test:  ## Run tests
	$(PYTEST) tests/ -vv

coverage:  ## Run tests with coverage report
	$(PYTEST) --cov=$(PACKAGE_NAME) \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-fail-under=$(COVERAGE_THRESHOLD)

build: clean coverage  ## Build package
	poetry build

publish: build  ## Publish package to PyPI
	python scripts/generate_instance_metadata.py
	poetry publish 
