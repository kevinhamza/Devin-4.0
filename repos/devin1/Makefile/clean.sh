#!/bin/bash

# Clean script for Devin project

echo "Starting clean process..."

# Remove Python cache files
echo "Removing Python cache files..."
find . -type f -name '*.pyc' -delete

# Remove temporary files
echo "Removing temporary files..."
find . -type f -name '*~' -delete
find . -type d -name '__pycache__' -exec rm -rf {} \;

# Remove build artifacts
echo "Removing build artifacts..."
make clean

echo "Clean process completed successfully."
