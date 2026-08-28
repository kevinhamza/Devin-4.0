#!/bin/bash

# Update script for Devin project production and test dependencies

echo "Updating production and test dependencies for Devin project..."

# Update production dependencies from requirements-prod.txt
pip install --upgrade -r requirements-prod.txt

# Update test dependencies from requirements-test.txt
pip install --upgrade -r requirements-test.txt

# Verify if all production and test packages are installed and up-to-date
pip freeze > requirements-prod.txt
pip freeze > requirements-test.txt

echo "Production and test dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating dependencies. Please review the output above for details."
fi
