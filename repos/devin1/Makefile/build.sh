#!/bin/bash

# Build script for Devin project

echo "Starting build process..."

# Clean previous build artifacts
echo "Cleaning previous build artifacts..."
make clean

# Compile and build project
echo "Compiling and building project..."
make build

# Run tests
echo "Running tests..."
make test

# Start the main application
echo "Starting main application..."
make run

echo "Build and run process completed successfully."
