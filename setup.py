# Devin/setup.py
# Purpose: Deployment configuration for the Devin AGI project.

from setuptools import setup, find_packages
from pathlib import Path

# Function to read the requirements.txt file
def read_requirements():
    """Reads the requirements.txt file and returns a list of dependencies."""
    return [
        line.strip()
        for line in Path("requirements.txt").read_text().splitlines()
        if not line.startswith("#")
    ]

setup(
    include_package_data=True,
)
