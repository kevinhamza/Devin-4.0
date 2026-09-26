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
    name="devin",
    version="4.0.0",
    author="Kevin Hamza",
    author_email="kevin.x.hamza@gmail.com",
    description="Devin 4.0: The most capable open-source autonomous AI agent — fully controls your OS, works with zero API keys",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/kevinhamza/Devin-4.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "devin=agent:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
    ],
    python_requires=">=3.9",
    include_package_data=True,
)
