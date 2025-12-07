#!/bin/bash
# Test runner script for Gemini PowerPoint Sage

echo "================================"
echo "Gemini PowerPoint Sage - Tests"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Checking if it can be installed...${NC}"
    
    # Try to install in virtual environment
    if [ -d ".venv" ]; then
        echo -e "${GREEN}Using existing virtual environment...${NC}"
        source .venv/bin/activate
    else
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv .venv
        source .venv/bin/activate
    fi
    
    echo -e "${GREEN}Installing test dependencies...${NC}"
    pip install -q pytest pytest-asyncio pytest-cov pytest-mock 2>&1 | grep -v "externally-managed" || {
        echo -e "${RED}Cannot install pytest in this environment.${NC}"
        echo -e "${YELLOW}Running syntax verification instead...${NC}"
        echo ""
        python3 verify_tests.py
        exit $?
    }
fi

echo ""
echo "================================"
echo "Running Tests"
echo "================================"
echo ""

# Parse command line arguments
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    unit)
        echo -e "${GREEN}Running unit tests only...${NC}"
        pytest tests/unit/ -v
        ;;
    integration)
        echo -e "${GREEN}Running integration tests only...${NC}"
        pytest tests/integration/ -v
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        pytest --cov=config --cov=services --cov=utils --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    quick)
        echo -e "${GREEN}Running quick tests (no coverage)...${NC}"
        pytest tests/ -v
        ;;
    verify)
        echo -e "${GREEN}Running syntax verification...${NC}"
        python3 verify_tests.py
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest tests/ -v
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|coverage|quick|verify|all]"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Tests completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Tests failed${NC}"
    exit 1
fi
