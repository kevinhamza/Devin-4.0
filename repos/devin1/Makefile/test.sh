#!/bin/bash

# Test script for Devin project

echo "Starting tests for Devin project..."

# Set up the environment
source .env  # Load environment variables

# Run tests (replace 'pytest' with your test runner if needed)
echo "Running tests..."
pytest

# Check the exit code of the test runner
if [ $? -eq 0 ]; then
    echo "All tests passed successfully."
else
    echo "Some tests failed. Please review the output above for details."
fi
