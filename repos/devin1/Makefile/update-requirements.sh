#!/bin/bash

# Update script for Devin project dependencies

echo "Updating dependencies for Devin project..."

# Install or update Python packages from requirements.txt
pip install --upgrade -r requirements.txt

# Verify if all packages are installed and up-to-date
pip freeze > requirements.txt

echo "Dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating dependencies. Please review the output above for details."
fi
