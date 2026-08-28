# Makefile for the Devin AGI Project

# Use a virtual environment
VENV_DIR=venv
PYTHON=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip

# Default target
all: install

# Create virtual environment and install dependencies
venv:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	python3 -m venv $(VENV_DIR)

install: venv
	@echo "Installing dependencies from requirements.txt..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "\nInstallation complete. Run 'source $(VENV_DIR)/bin/activate' to use the environment."

# Run the main application
run:
	@echo "Starting Devin AGI..."
	source $(VENV_DIR)/bin/activate && $(PYTHON) main.py

# Run all tests
test:
	@echo "Running all tests..."
	source $(VENV_DIR)/bin/activate && $(PYTHON) -m unittest discover -s tests

# Run performance benchmarks
benchmark:
	@echo "Running performance benchmarks..."
	source $(VENV_DIR)/bin/activate && $(PYTHON) tests/performance/benchmark_ai.py

# Run self-pentest
pentest:
	@echo "Running self-penetration test..."
	source $(VENV_DIR)/bin/activate && $(PYTHON) tests/pentesting/test_self_pentest.py

# Lint the code
lint:
	@echo "Linting the codebase..."
	$(PIP) install flake8
	$(VENV_DIR)/bin/flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Clean up build artifacts
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

.PHONY: all install venv run test benchmark pentest lint clean
