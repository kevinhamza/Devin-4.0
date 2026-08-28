"""
Remote Control Module
=====================
Handles remote operation of the robotics system, including manual control
via controllers, mobile apps, or web interfaces.
"""

import logging
import socket
import threading
from queue import Queue


class RemoteControlServer:
    """
    Remote control server to manage connections and commands from remote clients.
    """

    def __init__(self, host="0.0.0.0", port=9090):
        """
        Initializes the remote control server.

        Args:
            host (str): The host IP address to bind the server to.
            port (int): The port number to listen for incoming connections.
        """
        print("[INFO] Initializing Remote Control Server...")
        self.host = host
        self.port = port
        self.server_socket = None
        self.connections = []
        self.command_queue = Queue()
        self.running = False

    def start_server(self):
        """
        Starts the remote control server.
        """
        print("[INFO] Starting Remote Control Server...")
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            threading.Thread(target=self._accept_connections, daemon=True).start()
            print(f"[INFO] Remote Control Server started on {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Error starting server: {e}")

    def _accept_connections(self):
        """
        Accepts incoming connections from remote clients.
        """
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[INFO] Connection accepted from {address}")
                self.connections.append(client_socket)
                threading.Thread(
                    target=self._handle_client, args=(client_socket,), daemon=True
                ).start()
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

    def _handle_client(self, client_socket):
        """
        Handles communication with a connected client.

        Args:
            client_socket (socket.socket): The socket of the connected client.
        """
        try:
            while self.running:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                print(f"[INFO] Command received: {data}")
                self.command_queue.put(data)
            client_socket.close()
        except Exception as e:
            logging.error(f"Error handling client: {e}")

    def stop_server(self):
        """
        Stops the remote control server.
        """
        print("[INFO] Stopping Remote Control Server...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for conn in self.connections:
            conn.close()
        print("[INFO] Remote Control Server stopped.")

    def get_next_command(self):
        """
        Retrieves the next command from the command queue.

        Returns:
            str: The next command from the queue, or None if the queue is empty.
        """
        if not self.command_queue.empty():
            return self.command_queue.get()
        return None


class CommandHandler:
    """
    Processes and executes commands received from the remote control server.
    """

    def __init__(self, robot_controller):
        """
        Initializes the command handler.

        Args:
            robot_controller (object): The robot controller instance to execute commands.
        """
        print("[INFO] Initializing Command Handler...")
        self.robot_controller = robot_controller

    def execute_command(self, command):
        """
        Executes a given command.

        Args:
            command (str): The command string to execute.
        """
        print(f"[INFO] Executing command: {command}")
        try:
            if command == "MOVE_FORWARD":
                self.robot_controller.move_forward()
            elif command == "MOVE_BACKWARD":
                self.robot_controller.move_backward()
            elif command == "TURN_LEFT":
                self.robot_controller.turn_left()
            elif command == "TURN_RIGHT":
                self.robot_controller.turn_right()
            elif command == "STOP":
                self.robot_controller.stop()
            else:
                print(f"[WARNING] Unknown command: {command}")
        except Exception as e:
            logging.error(f"Error executing command: {e}")


# Example usage
if __name__ == "__main__":
    from modules.robotics.motor_control import MotorController  # Assuming motor_control.py defines MotorController

    class MockRobotController:
        """
        A mock robot controller for demonstration purposes.
        """

        def move_forward(self):
            print("[ROBOT] Moving forward.")

        def move_backward(self):
            print("[ROBOT] Moving backward.")

        def turn_left(self):
            print("[ROBOT] Turning left.")

        def turn_right(self):
            print("[ROBOT] Turning right.")

        def stop(self):
            print("[ROBOT] Stopping.")

    # Setup the remote control server and command handler
    server = RemoteControlServer(port=9091)
    robot_controller = MockRobotController()
    command_handler = CommandHandler(robot_controller)

    try:
        server.start_server()
        while True:
            command = server.get_next_command()
            if command:
                command_handler.execute_command(command)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        server.stop_server()
