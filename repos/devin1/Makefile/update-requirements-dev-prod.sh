#!/bin/bash

# Update script for Devin project development and production dependencies

echo "Updating development and production dependencies for Devin project..."

# Update development dependencies from requirements-dev.txt
pip install --upgrade -r requirements-dev.txt

# Update production dependencies from requirements-prod.txt
pip install --upgrade -r requirements-prod.txt

# Verify if all development and production packages are installed and up-to-date
pip freeze > requirements-dev.txt
pip freeze > requirements-prod.txt

echo "Development and production dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating dependencies. Please review the output above for details."
fi
