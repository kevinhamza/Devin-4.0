# modules/__init__.py

"""
Initializes all modules in the project. This file ensures that each module is properly loaded and ready for use.
It also provides utility functions to interact with and manage these modules dynamically.
"""

import importlib
import os
import pkgutil
import logging

# Setup logging for initialization process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dynamically import all submodules in the modules directory
def initialize_modules():
    """Dynamically loads all modules in the 'modules/' directory."""
    module_path = os.path.dirname(__file__)
    package_name = os.path.basename(module_path)

    logger.info(f"Initializing modules from package: {package_name}")

    for _, module_name, is_pkg in pkgutil.iter_modules([module_path]):
        full_module_name = f"{package_name}.{module_name}"
        try:
            if not is_pkg:
                logger.info(f"Loading module: {full_module_name}")
                importlib.import_module(full_module_name)
            else:
                logger.info(f"Found subpackage: {full_module_name}")
        except ImportError as e:
            logger.error(f"Failed to load module {full_module_name}: {e}")

# Exported functions and utilities from this package
__all__ = [
    "initialize_modules"
]
