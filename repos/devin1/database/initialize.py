import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the database
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'my_database.db')

# Function to initialize the database
def initialize_database():
    """Initialize the SQLite database."""
    try:
        # Check if database file exists
        if not os.path.exists(DATABASE_PATH):
            logger.info("Database file not found. Creating a new one...")

        # Create a connection to the database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Example: Create a table if it does not exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Example: Create another table if needed
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL
        );
        ''')

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        logger.info("Database initialized successfully.")
        return True

    except sqlite3.Error as e:
        logger.error(f"Error initializing the database: {e}")
        return False

# Initialize the database when this script is run directly
if __name__ == "__main__":
    if initialize_database():
        logger.info("Database setup complete.")
    else:
        logger.error("Failed to initialize the database.")
