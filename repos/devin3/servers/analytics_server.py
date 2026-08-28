# # Devin/servers/analytics_server.py
# # Purpose: A server that ingests real-time metrics, stores them historically,
# #          and provides an API for generating analytics reports and graphs.

# import logging
# import asyncio
# import threading
# import json
# import sqlite3
# from datetime import datetime, timedelta
# from pathlib import Path
# from io import BytesIO

# try:
#     from flask import Flask, request, jsonify, send_file
#     import pandas as pd
#     import matplotlib
#     matplotlib.use('Agg') # Use non-interactive backend
#     import matplotlib.pyplot as plt
#     import websockets
    
#     DEVIN_CORE_AVAILABLE = True
# except ImportError as e:
#     DEVIN_CORE_AVAILABLE = False
#     _import_error = e

# # Configure basic logging
# logger = logging.getLogger("AnalyticsServer")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)


# class AnalyticsServer:
#     """
#     Ingests, stores, and serves historical system performance data.
#     """
#     def __init__(self, db_path: Path, monitor_ws_url: str = "ws://127.0.0.1:8765"):
#         if not DEVIN_CORE_AVAILABLE:
#             raise ImportError(f"A required library is missing. Error: {_import_error}")

#         self.db_path = db_path
#         self.monitor_ws_url = monitor_ws_url
#         self._init_db()

#         # --- Ingestion Components ---
#         self._ingestor_thread = threading.Thread(target=self._run_ingestor, daemon=True)
        
#         # --- API Components ---
#         self.app = Flask(__name__)
#         self._register_routes()

#     def _init_db(self):
#         """Initializes the SQLite database and table."""
#         with sqlite3.connect(self.db_path) as conn:
#             cursor = conn.cursor()
#             cursor.execute("""
#             CREATE TABLE IF NOT EXISTS metrics (
#                 timestamp DATETIME PRIMARY KEY,
#                 cpu_percent REAL,
#                 memory_percent REAL,
#                 net_sent_mb REAL,
#                 net_recv_mb REAL
#             )
#             """)
#             conn.commit()
            
#     async def _ingestor_loop(self):
#         """Connects to the monitor server and ingests data into the DB."""
#         logger.info(f"Ingestor connecting to {self.monitor_ws_url}...")
#         async for websocket in websockets.connect(self.monitor_ws_url):
#             try:
#                 async for message in websocket:
#                     data = json.loads(message)
#                     with sqlite3.connect(self.db_path) as conn:
#                         cursor = conn.cursor()
#                         cursor.execute(
#                             "INSERT OR REPLACE INTO metrics VALUES (?, ?, ?, ?, ?)",
#                             (
#                                 datetime.now(),
#                                 data['cpu']['usage_percent'],
#                                 data['memory']['percent'],
#                                 data['network']['megabytes_sent'],
#                                 data['network']['megabytes_recv']
#                             )
#                         )
#                         conn.commit()
#             except websockets.ConnectionClosed:
#                 logger.warning("Connection to monitor server lost. Reconnecting in 5s...")
#                 await asyncio.sleep(5)
#             except Exception as e:
#                 logger.error(f"Ingestor error: {e}. Retrying in 15s...")
#                 await asyncio.sleep(15)

#     def _run_ingestor(self):
#         """Runs the asyncio event loop for the ingestor."""
#         asyncio.run(self._ingestor_loop())

#     def _register_routes(self):
#         """Defines the API endpoints for the server."""
#         @self.app.route("/report/<metric>.png")
#         def generate_report_plot(metric: str):
#             period = request.args.get("period", "1h") # e.g., 1h, 15m, 1d
            
#             # Simple parser for time period
#             value = int(period[:-1])
#             unit = period[-1]
#             if unit == 'h': delta = timedelta(hours=value)
#             elif unit == 'm': delta = timedelta(minutes=value)
#             elif unit == 'd': delta = timedelta(days=value)
#             else: return jsonify({"error": "Invalid period format. Use 'h', 'm', or 'd'."}), 400
            
#             cutoff_time = datetime.now() - delta
            
#             with sqlite3.connect(self.db_path) as conn:
#                 df = pd.read_sql_query(f"SELECT * FROM metrics WHERE timestamp >= '{cutoff_time}'", conn)

#             if df.empty:
#                 return jsonify({"error": "No data available for the selected period."}), 404
            
#             df['timestamp'] = pd.to_datetime(df['timestamp'])
#             df.set_index('timestamp', inplace=True)
            
#             metric_map = {
#                 "cpu": ("cpu_percent", "CPU Usage (%)"),
#                 "memory": ("memory_percent", "Memory Usage (%)"),
#             }
#             if metric not in metric_map:
#                 return jsonify({"error": f"Invalid metric. Available: {list(metric_map.keys())}"}), 400
            
#             col, ylabel = metric_map[metric]

#             plt.style.use('seaborn-v0_8-darkgrid')
#             fig, ax = plt.subplots(figsize=(12, 6))
#             df[col].plot(ax=ax, title=f'{ylabel} (Last {period})', legend=False)
#             ax.set_ylabel(ylabel)
#             ax.set_xlabel("Time")
#             fig.tight_layout()

#             buf = BytesIO()
#             fig.savefig(buf, format="png")
#             buf.seek(0)
#             plt.close(fig)

#             return send_file(buf, mimetype='image/png')
            
#     def start(self):
#         """Starts the data ingestor and the Flask server."""
#         self._ingestor_thread.start()
#         logger.warning(f"Starting Analytics Server on http://127.0.0.1:5004")
#         self.app.run(host='127.0.0.1', port=5004)


# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Analytics & Reporting Server Prototype 📊📈 ===")
#     print("=========================================================")
    
#     if not DEVIN_CORE_AVAILABLE:
#         print(f"\nERROR: A required library or module is missing. Please check your installation.")
#         print(f"Error: {_import_error}")
#     else:
#         # 1. Setup
#         db_file = Path("analytics.db")
#         if db_file.exists(): db_file.unlink()
        
#         print("!!! PREREQUISITE: This server requires the `system_monitor_server.py` to be running first. !!!")
#         print("\n1. In a separate terminal, run: python -m servers.system_monitor_server")
#         print("2. Once the monitor server is running, run this script.")
#         print("\nOnce this server is running, you can access the reports in your web browser:")
#         print("  - CPU Report (last hour): http://127.0.0.1:5004/report/cpu.png?period=1h")
#         print("  - Memory Report (last 10 mins): http://127.0.0.1:5004/report/memory.png?period=10m")
        
#         server = AnalyticsServer(db_path=db_file)
#         try:
#             server.start()
#         except KeyboardInterrupt:
#             logger.info("Server is shutting down.")
#         finally:
#             if db_file.exists(): db_file.unlink()

#     print("\n=========================================================")
#     print("=== Analytics Server Prototype Complete ===")
#     print("=========================================================")



# Devin/servers/analytics_server.py
# Purpose: A Flask-based server to handle real-time logging and retrieval
#          of time-series data for system analytics.

import logging
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import time

# (Logging setup assumed to be here)

class AnalyticsServer:
    """A server for logging and querying time-series event data."""
    def __init__(self, db_path: str = "analytics_data.feather"):
        self.app = Flask(__name__)
        self.db_path = Path(db_path)
        self.df = self._load_data()
        self._setup_routes()

    def _load_data(self) -> pd.DataFrame:
        """Loads the analytics data from a Feather file on startup."""
        if self.db_path.exists():
            logging.info(f"Loading existing analytics data from {self.db_path}")
            return pd.read_feather(self.db_path)
        else:
            logging.info("No existing analytics data found. Initializing new DataFrame.")
            return pd.DataFrame(columns=["timestamp", "event_type", "value"])

    def _save_data(self):
        """Saves the current DataFrame to a Feather file."""
        logging.info(f"Saving analytics data to {self.db_path}...")
        try:
            self.df.to_feather(self.db_path)
            logging.info("Analytics data saved successfully.")
        except Exception as e:
            logging.error(f"Failed to save analytics data: {e}")

    def _setup_routes(self):
        """Configures the API endpoints for the Flask app."""
        @self.app.route('/log', methods=['POST'])
        def log_event():
            # ... (log_event logic remains the same)
            data = request.json
            if not data or 'event_type' not in data or 'value' not in data or not isinstance(data['value'], (int, float)):
                return jsonify({"status": "error", "message": "Invalid payload"}), 400
            
            new_record = pd.DataFrame([{
                "timestamp": datetime.now(),
                "event_type": data['event_type'],
                "value": data['value']
            }])
            self.df = pd.concat([self.df, new_record], ignore_index=True)
            return jsonify({"status": "success"})

        @self.app.route('/data', methods=['GET'])
        def get_data():
            # ... (get_data logic remains the same)
            period = request.args.get('period', '5m')
            # (Parsing logic for period)
            # (Filtering logic for self.df)
            # This part is simplified for brevity
            return jsonify({"status": "data_placeholder"})

        @self.app.route('/reset', methods=['POST'])
        def reset_data():
            self.df = pd.DataFrame(columns=["timestamp", "event_type", "value"])
            return jsonify({"status": "reset"})

        @self.app.route('/shutdown', methods=['POST'])
        def shutdown():
            self._save_data() # Save data on shutdown
            func = request.environ.get('werkzeug.server.shutdown')
            if func:
                func()
            return 'Server shutting down...'

    def run(self, host='127.0.0.1', port=5004):
        logging.warning(f"Starting Analytics Server on http://{host}:{port}")
        self.app.run(host=host, port=port)
