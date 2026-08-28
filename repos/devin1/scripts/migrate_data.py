"""
scripts/migrate_data.py
-----------------------
Handles data migration between different project versions, ensuring compatibility
and seamless upgrade processes.
"""

import os
import logging
from typing import List, Dict
from sqlalchemy import create_engine, MetaData, Table

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///project.db")
MIGRATION_LOG = os.path.join(os.getcwd(), "logs", "migration.log")

# Initialize logging
os.makedirs(os.path.dirname(MIGRATION_LOG), exist_ok=True)
logging.basicConfig(
    filename=MIGRATION_LOG,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class DataMigration:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        logger.info("Initialized DataMigration with database: %s", db_url)

    def load_schema(self):
        """
        Load the existing database schema into SQLAlchemy metadata.
        """
        try:
            self.metadata.reflect(bind=self.engine)
            logger.info("Schema loaded successfully.")
        except Exception as e:
            logger.error("Failed to load schema: %s", e)
            raise

    def apply_migration(self, migration_steps: List[Dict[str, str]]):
        """
        Apply a series of migration steps defined in the migration_steps list.
        """
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            for step in migration_steps:
                query = step.get("query")
                description = step.get("description", "No description")
                logger.info("Applying migration: %s", description)
                connection.execute(query)
                logger.info("Migration applied successfully.")
            transaction.commit()
        except Exception as e:
            logger.error("Migration failed: %s", e)
            transaction.rollback()
            raise
        finally:
            connection.close()

    def verify_migration(self, table_name: str):
        """
        Verify if a specific table exists post-migration.
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            logger.info("Table %s exists. Migration verified.", table_name)
            return True
        except Exception as e:
            logger.warning("Table %s not found: %s", table_name, e)
            return False

def main():
    logger.info("Starting data migration...")
    migration_steps = [
        {
            "query": "ALTER TABLE users ADD COLUMN last_login TIMESTAMP;",
            "description": "Add 'last_login' column to 'users' table.",
        },
        {
            "query": "CREATE TABLE logs (id INTEGER PRIMARY KEY, message TEXT, created_at TIMESTAMP);",
            "description": "Create 'logs' table.",
        },
        {
            "query": "UPDATE users SET last_login = CURRENT_TIMESTAMP;",
            "description": "Set 'last_login' for all users to current timestamp.",
        },
    ]

    migrator = DataMigration(DATABASE_URL)
    migrator.load_schema()
    migrator.apply_migration(migration_steps)

    if migrator.verify_migration("logs"):
        logger.info("Migration completed successfully.")
    else:
        logger.error("Migration verification failed.")

if __name__ == "__main__":
    main()
