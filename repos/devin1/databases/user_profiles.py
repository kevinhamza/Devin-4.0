import sqlite3
from datetime import datetime

# Initialize the database connection
db_path = "databases/user_profiles.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Define the schema
def initialize_database():
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create roles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT UNIQUE NOT NULL,
        description TEXT
    );
    """)

    # Create user_roles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (role_id) REFERENCES roles (id),
        PRIMARY KEY (user_id, role_id)
    );
    """)

    # Create preferences table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preferences (
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        PRIMARY KEY (user_id, key)
    );
    """)

    # Insert default roles
    default_roles = [
        ("admin", "Administrator with full access"),
        ("user", "Regular user with limited access"),
        ("guest", "Guest user with minimal access")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?);
    """, default_roles)

    conn.commit()

# Add a new user
def add_user(username, email, password_hash):
    cursor.execute("""
    INSERT INTO users (username, email, password_hash) 
    VALUES (?, ?, ?);
    """, (username, email, password_hash))
    conn.commit()

# Assign a role to a user
def assign_role_to_user(user_id, role_id):
    cursor.execute("""
    INSERT OR IGNORE INTO user_roles (user_id, role_id)
    VALUES (?, ?);
    """, (user_id, role_id))
    conn.commit()

# Update user preferences
def update_user_preference(user_id, key, value):
    cursor.execute("""
    INSERT OR REPLACE INTO preferences (user_id, key, value)
    VALUES (?, ?, ?);
    """, (user_id, key, value))
    conn.commit()

# Main execution
if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at {db_path}")

    # Example: Add a sample user
    add_user("john_doe", "john@example.com", "hashed_password")
    print("Sample user 'john_doe' added.")

    # Example: Assign a role to the user
    assign_role_to_user(1, 1)  # Assigning "admin" role to user_id 1
    print("Role 'admin' assigned to user 'john_doe'.")

    # Example: Update user preference
    update_user_preference(1, "theme", "dark")
    print("User preference 'theme=dark' updated for user 'john_doe'.")

# Close the connection when done
conn.close()
