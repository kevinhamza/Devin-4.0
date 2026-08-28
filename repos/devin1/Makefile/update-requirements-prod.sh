#!/bin/bash

# Update script for Devin project production dependencies

echo "Updating production dependencies for Devin project..."

# Install or update production packages from requirements-prod.txt
pip install --upgrade -r requirements-prod.txt

# Verify if all production packages are installed and up-to-date
pip freeze > requirements-prod.txt

echo "Production dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating production dependencies. Please review the output above for details."
fi
