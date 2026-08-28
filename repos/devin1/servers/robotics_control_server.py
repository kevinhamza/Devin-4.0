# servers/robotics_control_server.py

import socket
import threading
import time
from config import robotics_config
from my_modules import robot_controller

# Function to handle client requests for robotics control
def handle_robot_control_request(client_socket):
    try:
        while True:
            request = client_socket.recv(robotics_config.BUFFER_SIZE).decode('utf-8')
            if not request:
                break

            # Process the request using robot controller
            response = robot_controller.execute_task(request)
            client_socket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling robotics control request: {e}")
    finally:
        client_socket.close()

# Function to start the robotics control server
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((robotics_config.HOST, robotics_config.PORT))
    server.listen(robotics_config.MAX_CONNECTIONS)
    print(f"Robotics Control Server started on {robotics_config.HOST}:{robotics_config.PORT}")

    while True:
        client_socket, client_address = server.accept()
        print(f"Connection established with {client_address}")
        client_handler = threading.Thread(target=handle_robot_control_request, args=(client_socket,))
        client_handler.start()

# Entry point for the robotics control server
if __name__ == "__main__":
    start_server()
