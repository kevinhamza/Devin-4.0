"""
Networking Module
Handles networking tasks such as API connections, data transfers, and communication protocols.
"""

import requests
import socket
from typing import Dict, Any, Optional


class APIManager:
    """
    Manages API connections and requests.
    """

    @staticmethod
    def send_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """
        Send an HTTP request to an API.

        Args:
            url (str): API endpoint.
            method (str): HTTP method (GET, POST, etc.).
            headers (Optional[Dict[str, str]]): Request headers.
            data (Optional[Dict[str, Any]]): Payload for POST/PUT requests.
            timeout (int): Timeout for the request in seconds.

        Returns:
            Dict[str, Any]: Response from the API.
        """
        try:
            print(f"Sending {method} request to {url}...")
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            print(f"Response received: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            return {"error": str(e)}


class NetworkUtility:
    """
    Provides utility functions for networking operations.
    """

    @staticmethod
    def get_ip_address(hostname: str) -> str:
        """
        Retrieve the IP address of a given hostname.

        Args:
            hostname (str): Hostname to resolve.

        Returns:
            str: IP address of the hostname.
        """
        try:
            print(f"Resolving IP address for {hostname}...")
            ip_address = socket.gethostbyname(hostname)
            print(f"IP address for {hostname}: {ip_address}")
            return ip_address
        except socket.error as e:
            print(f"Error resolving hostname {hostname}: {e}")
            return str(e)

    @staticmethod
    def check_port(host: str, port: int) -> bool:
        """
        Check if a port is open on a host.

        Args:
            host (str): Host address.
            port (int): Port number.

        Returns:
            bool: True if the port is open, False otherwise.
        """
        try:
            print(f"Checking port {port} on {host}...")
            with socket.create_connection((host, port), timeout=5):
                print(f"Port {port} on {host} is open.")
                return True
        except (socket.timeout, socket.error) as e:
            print(f"Port {port} on {host} is closed: {e}")
            return False


class FileTransfer:
    """
    Handles file transfer operations over the network.
    """

    @staticmethod
    def upload_file(url: str, file_path: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to a server.

        Args:
            url (str): Server endpoint for file upload.
            file_path (str): Path to the file to upload.
            headers (Optional[Dict[str, str]]): Request headers.

        Returns:
            Dict[str, Any]: Response from the server.
        """
        try:
            print(f"Uploading file {file_path} to {url}...")
            with open(file_path, "rb") as file:
                files = {"file": file}
                response = requests.post(url, headers=headers, files=files)
                response.raise_for_status()
                print(f"File uploaded successfully: {response.status_code}")
                return response.json()
        except (IOError, requests.exceptions.RequestException) as e:
            print(f"Error during file upload: {e}")
            return {"error": str(e)}

    @staticmethod
    def download_file(url: str, save_path: str) -> bool:
        """
        Download a file from a server.

        Args:
            url (str): URL of the file to download.
            save_path (str): Path to save the downloaded file.

        Returns:
            bool: True if download succeeds, False otherwise.
        """
        try:
            print(f"Downloading file from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"File downloaded successfully to {save_path}.")
            return True
        except (IOError, requests.exceptions.RequestException) as e:
            print(f"Error during file download: {e}")
            return False


# Example Usage
if __name__ == "__main__":
    api_manager = APIManager()
    network_util = NetworkUtility()
    file_transfer = FileTransfer()

    # Example API request
    api_response = api_manager.send_request(
        "https://jsonplaceholder.typicode.com/posts", method="GET"
    )
    print("API Response:", api_response)

    # Example networking utilities
    ip_address = network_util.get_ip_address("example.com")
    port_status = network_util.check_port("example.com", 80)

    # Example file transfers
    file_upload_response = file_transfer.upload_file(
        "https://example.com/upload", "path/to/file.txt"
    )
    file_download_status = file_transfer.download_file(
        "https://example.com/file.txt", "path/to/save/file.txt"
    )
