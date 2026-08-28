"""
scripts/initialize_db.py
Initializes databases with default values, ensuring all systems have the necessary baseline data.
"""

import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("db_init.log"), logging.StreamHandler()]
)

# Database configuration
DATABASE_PATHS = {
    "analytics": "databases/analytics.db",
    "user_profiles": "databases/user_profiles.db",
    "robot_configs": "databases/robot_configs.db",
    "activity_logs": "databases/activity_logs.db"
}

DEFAULT_DATA = {
    "analytics": [
        ("metric_name", "metric_value", "timestamp"),
        ("user_activity", 0, "2024-01-01 00:00:00"),
        ("system_health", 100, "2024-01-01 00:00:00")
    ],
    "user_profiles": [
        ("user_id", "username", "preferences", "created_at"),
        (1, "admin", '{"theme": "dark", "notifications": true}', "2024-01-01 00:00:00")
    ],
    "robot_configs": [
        ("robot_id", "config_name", "config_value", "updated_at"),
        (1, "default_speed", "1.0", "2024-01-01 00:00:00")
    ],
    "activity_logs": [
        ("log_id", "activity_type", "details", "timestamp"),
        (1, "Initialization", "Database setup completed", "2024-01-01 00:00:00")
    ]
}

def create_tables(connection, table_name, schema):
    """
    Creates a table with the specified schema if it does not exist.
    """
    try:
        connection.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
        logging.info(f"Table {table_name} checked/created successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error creating table {table_name}: {e}")
        raise

def insert_default_data(connection, table_name, data):
    """
    Inserts default data into the specified table.
    """
    try:
        placeholders = ", ".join(["?"] * len(data[0]))
        query = f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})"
        connection.executemany(query, data[1:])
        logging.info(f"Default data inserted into {table_name}.")
    except sqlite3.Error as e:
        logging.error(f"Error inserting data into {table_name}: {e}")
        raise

def initialize_database(db_path, data_key):
    """
    Initializes a specific database with the default data provided.
    """
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
        logging.info(f"Directory {os.path.dirname(db_path)} created.")

    try:
        with sqlite3.connect(db_path) as conn:
            logging.info(f"Connected to database at {db_path}.")
            table_name = DEFAULT_DATA[data_key][0][0]
            columns = ", ".join([f"{col} TEXT" for col in DEFAULT_DATA[data_key][0]])
            create_tables(conn, table_name, columns)
            insert_default_data(conn, table_name, DEFAULT_DATA[data_key])
    except Exception as e:
        logging.error(f"Failed to initialize database {db_path}: {e}")

if __name__ == "__main__":
    logging.info("Database initialization started.")
    for db_key, db_path in DATABASE_PATHS.items():
        try:
            initialize_database(db_path, db_key)
        except Exception as e:
            logging.error(f"Error initializing {db_key} database: {e}")
    logging.info("Database initialization completed.")
