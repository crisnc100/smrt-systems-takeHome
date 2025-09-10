#!/bin/bash

# Test Query Logic Script
# Run this to validate all query logic is working correctly

echo "=================================="
echo "QUERY LOGIC VALIDATION TEST SUITE"
echo "=================================="
echo ""

# Change to server directory
cd "$(dirname "$0")"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found"
    exit 1
fi

echo "Using Python: $PYTHON"
echo ""

# Run the test suite
echo "Running query logic tests..."
echo "---------------------------------"
$PYTHON run_tests.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed. Please review the output above."
fi

echo ""
echo "To run specific tests:"
echo "  $PYTHON -m unittest tests.test_queries.TestQueryLogic.test_intent_detection"
echo "  $PYTHON -m unittest tests.test_edge_cases.TestEdgeCases"
echo ""