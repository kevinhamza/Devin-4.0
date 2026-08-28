"""
Universal OS Operations Module
Provides cross-platform utilities for interacting with the operating system.
"""

import os
import platform
import shutil
from typing import List, Dict, Optional


class UniversalOperations:
    """
    Provides cross-platform OS operations for file management, system information, and utility tasks.
    """

    def __init__(self):
        self.os_name = platform.system()

    def get_system_info(self) -> Dict[str, str]:
        """
        Retrieve basic system information.

        Returns:
            Dict[str, str]: A dictionary containing system information.
        """
        return {
            "OS": self.os_name,
            "Release": platform.release(),
            "Version": platform.version(),
            "Processor": platform.processor(),
            "Machine": platform.machine(),
            "Node Name": platform.node(),
        }

    def list_directory(self, path: str = ".") -> List[str]:
        """
        List all files and directories in a given path.

        Args:
            path (str): The directory path. Defaults to the current directory.

        Returns:
            List[str]: A list of file and directory names.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"The path '{path}' does not exist.")
        return os.listdir(path)

    def create_directory(self, path: str) -> bool:
        """
        Create a new directory.

        Args:
            path (str): The directory path to create.

        Returns:
            bool: True if the directory was created successfully, False otherwise.
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False

    def delete_file_or_directory(self, path: str) -> bool:
        """
        Delete a file or directory.

        Args:
            path (str): The path to the file or directory to delete.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"The path '{path}' does not exist.")
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"Error deleting path: {e}")
            return False

    def copy_file(self, src: str, dest: str) -> bool:
        """
        Copy a file to a new location.

        Args:
            src (str): The source file path.
            dest (str): The destination file path.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if not os.path.isfile(src):
            raise FileNotFoundError(f"The source file '{src}' does not exist.")
        try:
            shutil.copy2(src, dest)
            return True
        except Exception as e:
            print(f"Error copying file: {e}")
            return False

    def move_file(self, src: str, dest: str) -> bool:
        """
        Move a file to a new location.

        Args:
            src (str): The source file path.
            dest (str): The destination file path.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if not os.path.isfile(src):
            raise FileNotFoundError(f"The source file '{src}' does not exist.")
        try:
            shutil.move(src, dest)
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False

    def get_disk_usage(self, path: str = "/") -> Dict[str, float]:
        """
        Get disk usage statistics for a given path.

        Args:
            path (str): The directory path. Defaults to root.

        Returns:
            Dict[str, float]: Disk usage in GB for total, used, and free space.
        """
        try:
            total, used, free = shutil.disk_usage(path)
            return {
                "Total (GB)": total / (1024 ** 3),
                "Used (GB)": used / (1024 ** 3),
                "Free (GB)": free / (1024 ** 3),
            }
        except Exception as e:
            print(f"Error fetching disk usage: {e}")
            return {}

    def find_files(self, directory: str, pattern: str) -> List[str]:
        """
        Find files in a directory matching a specific pattern.

        Args:
            directory (str): The directory to search in.
            pattern (str): The pattern to match.

        Returns:
            List[str]: A list of file paths that match the pattern.
        """
        import fnmatch
        matches = []
        for root, dirs, files in os.walk(directory):
            for filename in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, filename))
        return matches


# Example Usage
if __name__ == "__main__":
    ops = UniversalOperations()

    print("System Information:")
    print(ops.get_system_info())

    print("\nListing Current Directory:")
    print(ops.list_directory("."))

    print("\nCreating a Directory:")
    print(ops.create_directory("./test_directory"))

    print("\nDeleting a Directory:")
    print(ops.delete_file_or_directory("./test_directory"))

    print("\nGetting Disk Usage:")
    print(ops.get_disk_usage("/"))
