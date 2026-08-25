# Devin/modules/canvas_server.py
# Purpose: A real-time visual canvas server to display Devin's work,
#          logs, and media outputs.
#
# openclaw's own canvas (extensions/canvas/) presents structured "widget"
# documents -- not just scrolling log lines -- on a connected macOS panel
# via its own companion-app/A2UI renderer infrastructure. That hosting
# mechanism is macOS/companion-app-specific and has no real equivalent in
# a standalone Python service, so it isn't ported directly. The genuinely
# portable idea -- structured widget content instead of only plain log
# lines -- is what `widget()` below adds: typed cards (status/table/image)
# alongside the existing scrolling `log()`.

import logging
from typing import Any, List, Optional
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
                    .widget { margin: 8px 0; padding: 10px; border: 1px solid #333; border-radius: 5px; background: #252526; }
                    .widget-status { border-left: 4px solid #569cd6; }
                    .widget-status.ok { border-left-color: #4ec9b0; }
                    .widget-status.fail { border-left-color: #f44747; }
                    .widget table { border-collapse: collapse; width: 100%; }
                    .widget th, .widget td { border: 1px solid #333; padding: 4px 8px; text-align: left; font-family: monospace; font-size: 0.9em; }
                    .widget img { max-width: 100%; border-radius: 4px; }
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

                    // Structured widget content (status/table/image), built with
                    // DOM APIs rather than innerHTML string interpolation so
                    // widget data (which can come from tool output) can't inject
                    // markup into the page.
                    socket.on('widget', (data) => {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'widget widget-' + (data.type || 'text');

                        if (data.title) {
                            const title = document.createElement('strong');
                            title.innerText = data.title;
                            wrapper.appendChild(title);
                        }

                        if (data.type === 'status') {
                            wrapper.classList.add(data.ok ? 'ok' : 'fail');
                            const p = document.createElement('div');
                            p.innerText = data.message || '';
                            wrapper.appendChild(p);
                        } else if (data.type === 'table' && Array.isArray(data.rows)) {
                            const table = document.createElement('table');
                            for (const row of data.rows) {
                                const tr = document.createElement('tr');
                                for (const cell of row) {
                                    const td = document.createElement('td');
                                    td.innerText = String(cell);
                                    tr.appendChild(td);
                                }
                                table.appendChild(tr);
                            }
                            wrapper.appendChild(table);
                        } else if (data.type === 'image' && data.src) {
                            const img = document.createElement('img');
                            img.src = data.src;
                            img.alt = data.title || 'canvas image';
                            wrapper.appendChild(img);
                        } else {
                            const p = document.createElement('div');
                            p.innerText = data.message || '';
                            wrapper.appendChild(p);
                        }

                        canvas.appendChild(wrapper);
                        canvas.scrollTop = canvas.scrollHeight;
                    });
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

    def widget(self, widget_type: str, title: str = "", message: str = "", ok: bool = True,
               rows: Optional[List[List[Any]]] = None, src: str = ""):
        """
        Sends structured widget content to the live canvas -- 'status' (a
        pass/fail card), 'table' (rows of cells), or 'image' (a URL/data
        URI) -- instead of a plain scrolling log line. Useful for showing a
        scan result, a comparison table, or a screenshot Devin just took.
        """
        self.socketio.emit('widget', {
            "type": widget_type, "title": title, "message": message,
            "ok": ok, "rows": rows or [], "src": src,
        })

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
