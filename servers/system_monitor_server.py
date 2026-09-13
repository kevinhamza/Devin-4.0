# Devin/servers/system_monitor_server.py
# Purpose: A real-time WebSocket server that monitors and broadcasts
#          system health metrics (CPU, memory, network).

import logging
import asyncio
import json
from typing import Set

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    from modules.monitoring.cpu_usage import get_cpu_usage
    from modules.monitoring.memory_tracker import get_memory_info
    from modules.monitoring.network_monitor import get_network_stats
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("SystemMonitorServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class SystemMonitorServer:
    """
    A WebSocket server that broadcasts system health metrics.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        if not WEBSOCKETS_AVAILABLE or not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A required library or module is missing. WebSockets: {WEBSOCKETS_AVAILABLE}. Core Error: {_import_error}")
            
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

    async def _register(self, websocket):
        """Adds a new client to the set of connected clients."""
        self.connected_clients.add(websocket)
        logger.info(f"New client connected: {websocket.remote_address}")

    async def _unregister(self, websocket):
        """Removes a client from the set."""
        self.connected_clients.remove(websocket)
        logger.info(f"Client disconnected: {websocket.remote_address}")

    async def _broadcast_metrics(self):
        """The main loop to gather and broadcast metrics every second."""
        while True:
            try:
                # 1. Gather all metrics
                metrics = {
                    "cpu": get_cpu_usage(),
                    "memory": get_memory_info(),
                    "network": get_network_stats(),
                }
                
                # 2. Convert to JSON and broadcast to all clients
                message = json.dumps(metrics, indent=2)
                if self.connected_clients:
                    await websockets.broadcast(self.connected_clients, message)
                
                # 3. Wait for the next interval
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5) # Wait longer on error

    async def _connection_handler(self, websocket, path):
        """Handles a single client connection."""
        await self._register(websocket)
        try:
            # Keep the connection open until the client disconnects
            await websocket.wait_closed()
        finally:
            await self._unregister(websocket)

    async def start(self):
        """Starts the server and the metrics broadcasting task."""
        logger.warning(f"Starting System Monitor WebSocket Server on ws://{self.host}:{self.port}")
        
        # Create and run the background task for broadcasting
        broadcast_task = asyncio.create_task(self._broadcast_metrics())
        
        async with websockets.serve(self._connection_handler, self.host, self.port):
            await asyncio.Future()  # Run forever

# --- Example Usage ---
# This server is designed to be run as a standalone service.
# To test it, run this script. Then, run the client script below in a separate terminal.

CLIENT_SCRIPT_CONTENT = """
import asyncio
import websockets
import json

async def receive_metrics():
    uri = "ws://127.0.0.1:8765"
    async with websockets.connect(uri) as websocket:
        print(f"--- Connected to System Monitor Server at {uri} ---")
        print("--- Receiving real-time system metrics... (Press Ctrl+C to stop) ---")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                # Clear the screen for a cleaner display
                print(chr(27) + "[2J")
                print(json.dumps(data, indent=2))
            except websockets.ConnectionClosed:
                print("Connection to server closed.")
                break
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    try:
        asyncio.run(receive_metrics())
    except KeyboardInterrupt:
        print("\\nClient stopped.")
"""

if __name__ == "__main__":
    print("=========================================================")
    print("=== Real-Time System Monitor Server 📈💻 ===")
    print("=========================================================")
    
    if not WEBSOCKETS_AVAILABLE or not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A required library or module is missing. Please check your installation.")
        print(f"WebSockets: {WEBSOCKETS_AVAILABLE}, Core Error: {_import_error}")
    else:
        # Save the client script for the user to run
        client_file = Path("system_monitor_client.py")
        client_file.write_text(CLIENT_SCRIPT_CONTENT)
        
        print(f"This script will start the WebSocket server.")
        print("To see the real-time metrics, run the following command")
        print("in a NEW, SEPARATE terminal window:")
        print(f"\n  python {client_file}\n")

        server = SystemMonitorServer()
        try:
            asyncio.run(server.start())
        except KeyboardInterrupt:
            logger.info("Server is shutting down.")
        finally:
            if client_file.exists():
                client_file.unlink()

    print("\n=========================================================")
    print("=== System Monitor Server Complete ===")
    print("=========================================================")
