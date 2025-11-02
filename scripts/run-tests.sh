#!/bin/bash
# Helper script to run all tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Running Test Suite ==="
echo ""

# Python unit tests
echo "1. Running Python unit tests..."
python -m pytest tests/ -v || echo "??  Unit tests failed (continuing)"

# Docker Compose integration tests
echo ""
echo "2. Running integration tests..."
docker-compose up -d
sleep 10
python test_app.py || echo "??  Integration tests failed (continuing)"
docker-compose down

# Terraform validation
echo ""
echo "3. Validating Terraform..."
if command -v terraform &> /dev/null; then
    terraform init -backend=false
    terraform validate
    terraform fmt -check
else
    echo "??  Terraform not installed, skipping"
fi

echo ""
echo "? Test suite completed"
