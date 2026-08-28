import sqlite3
import os
from datetime import datetime

DB_PATH = "databases/logs.db"

# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Create the logs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT CHECK(log_level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL')) NOT NULL,
    module_name TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
connection.commit()


def add_log_entry(log_level, module_name, message):
    """
    Add a new log entry to the database.
    """
    cursor.execute("""
    INSERT INTO logs (log_level, module_name, message)
    VALUES (?, ?, ?)
    """, (log_level, module_name, message))
    connection.commit()
    print(f"Log entry added: [{log_level}] {module_name} - {message}")


def get_logs_by_level(log_level):
    """
    Retrieve logs filtered by a specific log level.
    """
    cursor.execute("""
    SELECT * FROM logs WHERE log_level = ? ORDER BY timestamp DESC
    """, (log_level,))
    return cursor.fetchall()


def get_logs_by_module(module_name):
    """
    Retrieve logs filtered by module name.
    """
    cursor.execute("""
    SELECT * FROM logs WHERE module_name = ? ORDER BY timestamp DESC
    """, (module_name,))
    return cursor.fetchall()


def get_all_logs():
    """
    Retrieve all logs from the database.
    """
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
    return cursor.fetchall()


def delete_old_logs(days_old):
    """
    Delete logs older than a specified number of days.
    """
    threshold_date = datetime.now() - timedelta(days=days_old)
    cursor.execute("DELETE FROM logs WHERE timestamp < ?", (threshold_date,))
    connection.commit()
    print(f"Logs older than {days_old} days have been deleted.")


# Test the implementation (if required)
if __name__ == "__main__":
    # Add sample logs
    add_log_entry("INFO", "authentication", "User login successful.")
    add_log_entry("ERROR", "file_manager", "Failed to open the requested file.")
    add_log_entry("DEBUG", "scheduler", "Task scheduling debug info.")

    # Retrieve and display all logs
    logs = get_all_logs()
    for log in logs:
        print(log)

    # Retrieve logs filtered by level
    error_logs = get_logs_by_level("ERROR")
    for log in error_logs:
        print(f"Error Log: {log}")

    # Retrieve logs filtered by module
    module_logs = get_logs_by_module("authentication")
    for log in module_logs:
        print(f"Module Log: {log}")

    # Delete logs older than 30 days (uncomment to test)
    # delete_old_logs(30)

# Close the database connection
connection.close()
