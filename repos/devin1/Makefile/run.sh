#!/bin/bash

# Run script for Devin project

echo "Starting the Devin project..."

# Set up the environment
source .env  # Load environment variables

# Run the main application
echo "Running the main application..."
python main.py

# Keep the server running (if applicable)
# Adjust the following command based on your specific needs (e.g., using a web server or process manager)
# Example: python manage.py runserver
# Example: gunicorn --workers 3 --bind 0.0.0.0:8000 myproject.wsgi:application

echo "Devin project is now running. Press Ctrl+C to stop."
