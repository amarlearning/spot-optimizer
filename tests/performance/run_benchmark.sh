#!/bin/bash

# Exit on error
set -e

echo "Cleaning up..."
make clean

echo "Creating fresh virtual environment for performance testing..."
python3 -m venv .venv-perf-test
source .venv-perf-test/bin/activate

echo "Building spot-optimizer wheel..."
poetry build

echo "Installing spot-optimizer wheel in test environment..."
pip install dist/spot_optimizer-*.whl

echo "Installing test dependencies..."
pip install statistics

echo "show python version"
python --version

echo "show pip dependencies"
pip freeze

sleep 10

echo "Generating test data..."
python tests/performance/generate_test_data.py

sleep 20

echo "Running performance tests..."
python tests/performance/benchmark_queries.py > tests/performance/benchmark_queries.log

echo "Cleaning up..."
deactivate
rm -rf .venv-perf-test

echo "Performance testing completed!" 