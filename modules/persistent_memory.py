"""
modules/persistent_memory.py — Persistent memory system with database backend

Provides long-term memory storage across sessions using SQLite.
Stores facts, context, relationships, and metadata.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib

# Database location
DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"


class PersistentMemory:
    """Persistent memory system backed by SQLite database"""

    def __init__(self, db_path: Path = DB_PATH):
        """Initialize persistent memory system"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Facts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 1.0
                )
            """)

            # Relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    object TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Context table (session-specific memory)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    expires_at TIMESTAMP
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships ON relationships(subject, relation)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_session ON context(session_id)")

            conn.commit()

    def save_fact(self, key: str, value: Any, category: str = "general",
                  tags: List[str] = None, confidence: float = 1.0) -> bool:
        """Save or update a fact"""
        try:
            value_json = json.dumps(value) if not isinstance(value, str) else value
            tags_json = json.dumps(tags or [])

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO facts (key, value, category, tags, confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        category = excluded.category,
                        tags = excluded.tags,
                        confidence = excluded.confidence,
                        updated_at = CURRENT_TIMESTAMP
                """, (key, value_json, category, tags_json, confidence))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving fact: {e}")
            return False

    def recall_fact(self, key: str) -> Optional[Any]:
        """Retrieve a fact by key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT value FROM facts WHERE key = ?
                """, (key,))
                result = cursor.fetchone()

                if result:
                    # Update access count
                    cursor.execute("UPDATE facts SET access_count = access_count + 1 WHERE key = ?", (key,))
                    conn.commit()

                    # Try to parse as JSON
                    try:
                        return json.loads(result[0])
                    except:
                        return result[0]
            return None
        except Exception as e:
            print(f"Error recalling fact: {e}")
            return None

    def search_facts(self, query: str, category: str = None, limit: int = 10) -> List[Dict]:
        """Search facts by keyword"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute("""
                        SELECT key, value, category, confidence, created_at
                        FROM facts
                        WHERE (key LIKE ? OR value LIKE ?) AND category = ?
                        ORDER BY access_count DESC, confidence DESC
                        LIMIT ?
                    """, (f"%{query}%", f"%{query}%", category, limit))
                else:
                    cursor.execute("""
                        SELECT key, value, category, confidence, created_at
                        FROM facts
                        WHERE key LIKE ? OR value LIKE ?
                        ORDER BY access_count DESC, confidence DESC
                        LIMIT ?
                    """, (f"%{query}%", f"%{query}%", limit))

                results = []
                for row in cursor.fetchall():
                    try:
                        value = json.loads(row[1])
                    except:
                        value = row[1]

                    results.append({
                        'key': row[0],
                        'value': value,
                        'category': row[2],
                        'confidence': row[3],
                        'created_at': row[4]
                    })

                return results
        except Exception as e:
            print(f"Error searching facts: {e}")
            return []

    def save_relationship(self, subject: str, relation: str, object: str,
                         weight: float = 1.0) -> bool:
        """Save a relationship between facts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO relationships (subject, relation, object, weight)
                    VALUES (?, ?, ?, ?)
                """, (subject, relation, object, weight))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving relationship: {e}")
            return False

    def find_related(self, subject: str, relation: str = None) -> List[Dict]:
        """Find facts related to a subject"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if relation:
                    cursor.execute("""
                        SELECT object, relation, weight FROM relationships
                        WHERE subject = ? AND relation = ?
                        ORDER BY weight DESC
                    """, (subject, relation))
                else:
                    cursor.execute("""
                        SELECT object, relation, weight FROM relationships
                        WHERE subject = ?
                        ORDER BY weight DESC
                    """, (subject,))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'object': row[0],
                        'relation': row[1],
                        'weight': row[2]
                    })

                return results
        except Exception as e:
            print(f"Error finding relationships: {e}")
            return []

    def list_facts(self, category: str = None, limit: int = 50) -> List[Dict]:
        """List all facts, optionally filtered by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute("""
                        SELECT key, value, category, confidence, access_count, created_at
                        FROM facts
                        WHERE category = ?
                        ORDER BY access_count DESC, updated_at DESC
                        LIMIT ?
                    """, (category, limit))
                else:
                    cursor.execute("""
                        SELECT key, value, category, confidence, access_count, created_at
                        FROM facts
                        ORDER BY access_count DESC, updated_at DESC
                        LIMIT ?
                    """, (limit,))

                results = []
                for row in cursor.fetchall():
                    try:
                        value = json.loads(row[1])
                    except:
                        value = row[1]

                    results.append({
                        'key': row[0],
                        'value': value,
                        'category': row[2],
                        'confidence': row[3],
                        'access_count': row[4],
                        'created_at': row[5]
                    })

                return results
        except Exception as e:
            print(f"Error listing facts: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM facts")
                fact_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM relationships")
                relation_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT category) FROM facts")
                category_count = cursor.fetchone()[0]

                cursor.execute("SELECT SUM(access_count) FROM facts")
                total_accesses = cursor.fetchone()[0] or 0

                return {
                    'facts_count': fact_count,
                    'relationships_count': relation_count,
                    'categories_count': category_count,
                    'total_accesses': total_accesses,
                    'db_path': str(self.db_path),
                    'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

    def clear_facts(self, category: str = None) -> bool:
        """Clear facts, optionally by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if category:
                    cursor.execute("DELETE FROM facts WHERE category = ?", (category,))
                else:
                    cursor.execute("DELETE FROM facts")

                conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing facts: {e}")
            return False


# Global instance
_memory = None

def get_memory() -> PersistentMemory:
    """Get or create global memory instance"""
    global _memory
    if _memory is None:
        _memory = PersistentMemory()
    return _memory


# Tool functions for TOOL_REGISTRY

def memory_save_persistent(key: str, value: Any, category: str = "general") -> bool:
    """Save fact to persistent memory"""
    return get_memory().save_fact(key, value, category)

def memory_recall_persistent(key: str) -> Optional[Any]:
    """Recall fact from persistent memory"""
    return get_memory().recall_fact(key)

def memory_search(query: str, category: str = None, limit: int = 10) -> List[Dict]:
    """Search persistent memory"""
    return get_memory().search_facts(query, category, limit)

def memory_list_persistent(category: str = None, limit: int = 50) -> List[Dict]:
    """List facts from persistent memory"""
    return get_memory().list_facts(category, limit)

def memory_stats() -> Dict[str, Any]:
    """Get memory statistics"""
    return get_memory().get_stats()

def memory_relate(subject: str, relation: str, object: str, weight: float = 1.0) -> bool:
    """Create relationship between facts"""
    return get_memory().save_relationship(subject, relation, object, weight)

def memory_find_related(subject: str, relation: str = None) -> List[Dict]:
    """Find related facts"""
    return get_memory().find_related(subject, relation)
