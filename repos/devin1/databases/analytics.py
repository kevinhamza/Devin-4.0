import sqlite3
from datetime import datetime

def initialize_analytics_db():
    conn = sqlite3.connect("databases/analytics.db")
    cursor = conn.cursor()

    # Create user activity table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        activity TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create module usage table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS module_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_name TEXT NOT NULL,
        user_id TEXT NOT NULL,
        usage_count INTEGER DEFAULT 0,
        last_used DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create task metrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT NOT NULL,
        user_id TEXT NOT NULL,
        execution_time REAL NOT NULL,
        status TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create error logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS error_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_name TEXT NOT NULL,
        error_message TEXT NOT NULL,
        user_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Analytics database initialized successfully.")

def log_user_activity(user_id, activity):
    conn = sqlite3.connect("databases/analytics.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_activity (user_id, activity) VALUES (?, ?)
    """, (user_id, activity))
    conn.commit()
    conn.close()

def log_module_usage(module_name, user_id):
    conn = sqlite3.connect("databases/analytics.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO module_usage (module_name, user_id, usage_count, last_used)
    VALUES (?, ?, 1, ?) ON CONFLICT(module_name, user_id) DO UPDATE
    SET usage_count = usage_count + 1, last_used = ?
    """, (module_name, user_id, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()

def log_task_metrics(task_name, user_id, execution_time, status):
    conn = sqlite3.connect("databases/analytics.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO task_metrics (task_name, user_id, execution_time, status)
    VALUES (?, ?, ?, ?)
    """, (task_name, user_id, execution_time, status))
    conn.commit()
    conn.close()

def log_error(module_name, error_message, user_id=None):
    conn = sqlite3.connect("databases/analytics.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO error_logs (module_name, error_message, user_id)
    VALUES (?, ?, ?)
    """, (module_name, error_message, user_id))
    conn.commit()
    conn.close()

# Initialize the database
if __name__ == "__main__":
    initialize_analytics_db()
