#!/bin/bash
set -e

# SaltBitter Test Runner Script
# Runs all tests: unit, integration, E2E, security, and performance

echo "========================================="
echo "  SaltBitter Testing Suite"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
FAILED=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${YELLOW}Running: ${test_name}${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✓ ${test_name} passed${NC}\n"
    else
        echo -e "${RED}✗ ${test_name} failed${NC}\n"
        FAILED=$((FAILED + 1))
    fi
}

# Change to project root
cd "$(dirname "$0")/.."

echo "Step 1: Backend Unit Tests"
echo "====================================="
run_test "Backend Unit Tests" "cd backend && pytest -v --cov --cov-report=term-missing --cov-fail-under=85 -m 'not integration and not e2e and not performance'"

echo "Step 2: Backend Integration Tests"
echo "====================================="
run_test "Backend Integration Tests" "cd backend && pytest -v -m integration"

echo "Step 3: Backend E2E Tests"
echo "====================================="
run_test "Backend E2E Tests" "cd backend && pytest -v -m e2e"

echo "Step 4: Backend Type Checking"
echo "====================================="
run_test "MyPy Type Checking" "cd backend && mypy --strict services/"

echo "Step 5: Backend Linting"
echo "====================================="
run_test "Ruff Linting" "cd backend && ruff check ."

echo "Step 6: Security Scanning"
echo "====================================="
run_test "Bandit Security Scan" "cd backend && bandit -r services/ -ll"

echo "Step 7: Frontend Linting"
echo "====================================="
run_test "ESLint Linting" "cd frontend && npm run lint"

echo "Step 8: Frontend Type Checking"
echo "====================================="
run_test "TypeScript Checking" "cd frontend && npx tsc --noEmit"

echo "Step 9: Frontend Unit Tests"
echo "====================================="
run_test "Frontend Unit Tests" "cd frontend && npm test -- --coverage --watchAll=false"

echo "Step 10: Frontend E2E Tests"
echo "====================================="
run_test "Playwright E2E Tests" "cd frontend && npx playwright test"

echo "Step 11: Performance Benchmarks"
echo "====================================="
run_test "Performance Tests" "cd backend && pytest -v -m performance"

echo "Step 12: Security Audit"
echo "====================================="
run_test "NPM Security Audit" "cd frontend && npm audit --audit-level=moderate"

echo ""
echo "========================================="
echo "  Test Summary"
echo "========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED test suite(s) failed${NC}"
    exit 1
fi
