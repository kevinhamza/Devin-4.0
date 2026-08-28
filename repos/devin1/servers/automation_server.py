# servers/automation_server.py

import socket
import threading
import time
from config import global_settings, ai_config
from my_modules import workflow_manager

# Function to handle client requests for automation
def handle_client_request(client_socket):
    try:
        while True:
            request = client_socket.recv(global_settings.BUFFER_SIZE).decode('utf-8')
            if not request:
                break

            # Process the request using workflow manager
            response = workflow_manager.process_request(request)
            client_socket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling client request: {e}")
    finally:
        client_socket.close()

# Function to start the automation server
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((global_settings.HOST, global_settings.PORT))
    server.listen(global_settings.MAX_CONNECTIONS)
    print(f"Automation Server started on {global_settings.HOST}:{global_settings.PORT}")

    while True:
        client_socket, client_address = server.accept()
        print(f"Connection established with {client_address}")
        client_handler = threading.Thread(target=handle_client_request, args=(client_socket,))
        client_handler.start()

# Entry point for the automation server
if __name__ == "__main__":
    start_server()
