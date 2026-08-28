#!/bin/bash

# Update script for Devin project

echo "Updating Devin project..."

# Pull the latest changes from the remote repository
git pull origin main

# Install or update Python packages from requirements.txt
pip install -r requirements.txt

# Run any necessary database migrations
python manage.py migrate

# Restart services if needed (adjust according to your project setup)
# systemctl restart your-service-name

echo "Devin project updated successfully."

# Check the status of services to confirm restart (optional)
# systemctl status your-service-name

# Ensure error-free deployment
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred during the update. Please review the output above for details."
fi
