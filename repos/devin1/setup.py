from setuptools import setup, find_packages
import os
import sys

# Read version info from a central version file
def get_version():
    with open("VERSION", "r") as version_file:
        return version_file.read().strip()

# Read long description from README.md
def get_long_description():
    with open("README.md", "r", encoding="utf-8") as readme_file:
        return readme_file.read()

# Determine dependencies dynamically based on OS
def get_install_requires():
    base_dependencies = [
        "numpy",
        "pandas",
        "scikit-learn",
        "opencv-python",
        "tensorflow",
        "torch",
        "transformers",
        "flask",
        "django",
        "fastapi",
        "pytest",
        "pytest-cov",
        "requests",
        "pyyaml",
        "boto3",
        "google-cloud",
        "azure-storage-blob",
    ]

    if sys.platform.startswith("win"):
        base_dependencies.append("pywin32")
    elif sys.platform.startswith("linux"):
        base_dependencies.append("pycairo")
    
    return base_dependencies

# Define console scripts for command-line usage
def get_entry_points():
    return {
        "console_scripts": [
            "devin=main:main",
            "devin-cli=scripts.robot_manager:main",
            "devin-server=scripts.server:start_server",
        ],
    }

setup(
    name="Devin",
    version=get_version(),
    author="Kevin Hamza",
    author_email="kevin.x.hamza@gmail.com",
    description="Devin AI - The most powerful and versatile AI assistant.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/your_username/devin",
    packages=find_packages(include=["devin", "devin.*"]),
    include_package_data=True,
    install_requires=get_install_requires(),
    extras_require={
        "dev": ["black", "flake8", "mypy", "pre-commit"],
        "test": ["pytest", "tox", "pytest-mock"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
    },
    entry_points=get_entry_points(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="AI, chatbot, automation, penetration testing, ethical hacking, robotics",
    project_urls={
        "Documentation": "https://your_project_docs_link",
        "Source": "https://github.com/your_username/devin",
        "Tracker": "https://github.com/your_username/devin/issues",
    },
    data_files=[
        ("configs", ["config/config.yaml"]),
        ("docs", ["docs/README.md", "docs/CONTRIBUTING.md"]),
        ("scripts", ["scripts/install.sh", "scripts/setup.bat"]),
    ],
    zip_safe=False,
)
