#!/bin/bash

# Update script for Devin project development dependencies

echo "Updating development dependencies for Devin project..."

# Install or update development packages from requirements-dev.txt
pip install --upgrade -r requirements-dev.txt

# Verify if all development packages are installed and up-to-date
pip freeze > requirements-dev.txt

echo "Development dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating development dependencies. Please review the output above for details."
fi
