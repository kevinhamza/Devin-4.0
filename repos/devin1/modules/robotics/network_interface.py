"""
Network Interface Module
========================
Handles network communication and remote interactions for the robotics system,
enabling seamless integration with external devices and cloud services.
"""

import socket
import threading
import logging
import requests
import json
from modules.utils.security import encrypt_data, decrypt_data

class NetworkInterface:
    """
    Manages network communication, including sending and receiving data,
    remote control, and integration with cloud services.
    """

    def __init__(self, host="0.0.0.0", port=8080, cloud_endpoint=None):
        """
        Initializes the network interface.

        Args:
            host (str): The hostname or IP address for local server setup.
            port (int): The port number for communication.
            cloud_endpoint (str): Optional endpoint for cloud services.
        """
        self.host = host
        self.port = port
        self.cloud_endpoint = cloud_endpoint
        self.server_socket = None
        self.clients = []
        self.running = False
        logging.info("Network interface initialized.")

    def start_server(self):
        """
        Starts the server to listen for incoming connections.
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            logging.info(f"Server started on {self.host}:{self.port}")

            threading.Thread(target=self._accept_clients, daemon=True).start()
        except Exception as e:
            logging.error(f"Error starting server: {e}")

    def _accept_clients(self):
        """
        Accepts incoming client connections.
        """
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                logging.info(f"New client connected: {client_address}")
                threading.Thread(
                    target=self._handle_client, args=(client_socket, client_address), daemon=True
                ).start()
            except Exception as e:
                logging.error(f"Error accepting client connection: {e}")

    def _handle_client(self, client_socket, client_address):
        """
        Handles communication with a connected client.

        Args:
            client_socket (socket.socket): The client's socket.
            client_address (tuple): The client's address.
        """
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                decrypted_data = decrypt_data(data)
                logging.info(f"Received data from {client_address}: {decrypted_data}")
                response = self.process_request(decrypted_data)
                client_socket.send(encrypt_data(response))
        except Exception as e:
            logging.error(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            self.clients.remove(client_socket)
            logging.info(f"Client {client_address} disconnected.")

    def process_request(self, request_data):
        """
        Processes incoming requests from clients.

        Args:
            request_data (str): The data received from the client.

        Returns:
            str: The response to send back to the client.
        """
        try:
            request = json.loads(request_data)
            command = request.get("command", "unknown")
            logging.info(f"Processing command: {command}")

            if command == "status":
                return json.dumps({"status": "online"})
            elif command == "control":
                action = request.get("action", "none")
                logging.info(f"Executing control action: {action}")
                return json.dumps({"result": f"Executed {action}"})
            else:
                return json.dumps({"error": "Unknown command"})
        except Exception as e:
            logging.error(f"Error processing request: {e}")
            return json.dumps({"error": "Invalid request"})

    def stop_server(self):
        """
        Stops the server and disconnects all clients.
        """
        self.running = False
        for client in self.clients:
            client.close()
        if self.server_socket:
            self.server_socket.close()
        logging.info("Server stopped.")

    def send_to_cloud(self, data):
        """
        Sends data to the cloud endpoint.

        Args:
            data (dict): The data to send.

        Returns:
            dict: The response from the cloud.
        """
        if not self.cloud_endpoint:
            logging.error("No cloud endpoint configured.")
            return {"error": "Cloud endpoint not configured"}

        try:
            encrypted_data = encrypt_data(json.dumps(data))
            response = requests.post(self.cloud_endpoint, data=encrypted_data)
            logging.info("Data sent to cloud.")
            return json.loads(decrypt_data(response.content))
        except Exception as e:
            logging.error(f"Error sending data to cloud: {e}")
            return {"error": "Failed to send data"}

# Example Usage
if __name__ == "__main__":
    network_interface = NetworkInterface(cloud_endpoint="https://api.example.com")
    network_interface.start_server()
    try:
        while True:
            pass  # Keep the server running
    except KeyboardInterrupt:
        network_interface.stop_server()
