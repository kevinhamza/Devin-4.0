# Devin/modules/canvas_server.py
# Purpose: A real-time visual canvas server to display Devin's work,
#          logs, and media outputs. Ported from OpenClaw's A2UI.

import logging
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import os
import threading

logger = logging.getLogger("CanvasServer")

class CanvasServer:
    def __init__(self, port: int = 5005):
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'devin_secret!'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self._setup_routes()
        self._setup_socket_events()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Devin AGI - Live Canvas</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
                <style>
                    body { font-family: sans-serif; background: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }
                    #canvas { border: 1px solid #333; background: #000; height: 70vh; overflow-y: auto; padding: 10px; border-radius: 5px; }
                    .log-entry { margin-bottom: 5px; font-family: monospace; }
                    .info { color: #569cd6; }
                    .success { color: #4ec9b0; }
                    .error { color: #f44747; }
                    h1 { color: #ce9178; }
                </style>
            </head>
            <body>
                <h1>🦞 Devin AGI - Live Canvas</h1>
                <div id="status">Connecting...</div>
                <div id="canvas"></div>
                <script>
                    const socket = io();
                    const canvas = document.getElementById('canvas');
                    const status = document.getElementById('status');

                    socket.on('connect', () => { status.innerText = 'Connected'; status.style.color = '#4ec9b0'; });
                    socket.on('disconnect', () => { status.innerText = 'Disconnected'; status.style.color = '#f44747'; });

                    socket.on('update', (data) => {
                        const div = document.createElement('div');
                        div.className = 'log-entry ' + (data.level || 'info');
                        div.innerText = `[${new Date().toLocaleTimeString()}] ${data.message}`;
                        canvas.appendChild(div);
                        canvas.scrollTop = canvas.scrollHeight;
                    });

                    socket.on('clear', () => { canvas.innerHTML = ''; });
                </script>
            </body>
            </html>
            """

    def _setup_socket_events(self):
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Client connected to Canvas")

    def log(self, message: str, level: str = "info"):
        """Sends a log message to the live canvas."""
        self.socketio.emit('update', {'message': message, 'level': level})

    def clear(self):
        """Clears the live canvas."""
        self.socketio.emit('clear', {})

    def run(self, host: str = "0.0.0.0"):
        logger.info(f"Starting Canvas Server on http://{host}:{self.port}")
        self.socketio.run(self.app, host=host, port=self.port, allow_unsafe_werkzeug=True)

    def start_background(self):
        """Starts the server in a daemon thread."""
        threading.Thread(target=self.run, daemon=True).start()

# --- Example Usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    canvas = CanvasServer()
    canvas.run()
