#!/bin/bash

# Update script for Devin project test dependencies

echo "Updating test dependencies for Devin project..."

# Install or update test packages from requirements-test.txt
pip install --upgrade -r requirements-test.txt

# Verify if all test packages are installed and up-to-date
pip freeze > requirements-test.txt

echo "Test dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating test dependencies. Please review the output above for details."
fi
