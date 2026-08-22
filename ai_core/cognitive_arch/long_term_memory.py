# Devin/ai_core/cognitive_arch/long_term_memory.py

import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import os
import json
import numpy as np

# Try to import sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    EMBEDDING_DIMENSION = 384
    print(f"Initialized local embedding model: {EMBEDDING_MODEL_NAME}")
except ImportError:
    embedding_model = None
    EMBEDDING_DIMENSION = 384 # Default
    print("Warning: sentence-transformers not found. Using placeholder embeddings.")

class LocalVectorDB:
    """A simple local vector database for persistent storage."""
    def __init__(self, storage_path: str = "ltm_storage.json"):
        self.storage_path = storage_path
        self.data: List[Dict[str, Any]] = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading LTM storage: {e}")
        return []

    def _save_data(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving LTM storage: {e}")

    def upsert(self, memory_id: str, embedding: List[float], metadata: Dict[str, Any], namespace: str):
        # Check if exists
        for item in self.data:
            if item['id'] == memory_id:
                item['embedding'] = embedding
                item['metadata'] = metadata
                item['namespace'] = namespace
                self._save_data()
                return
        
        self.data.append({
            'id': memory_id,
            'embedding': embedding,
            'metadata': metadata,
            'namespace': namespace
        })
        self._save_data()

    def query(self, query_embedding: List[float], top_k: int, namespace: str, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        results = []
        q_vec = np.array(query_embedding)

        for item in self.data:
            if item['namespace'] != namespace:
                continue
            
            # Simple metadata filter
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if item['metadata'].get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            i_vec = np.array(item['embedding'])
            # Cosine similarity
            similarity = np.dot(q_vec, i_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(i_vec) + 1e-9)
            
            results.append({
                'id': item['id'],
                'score': float(similarity),
                'metadata': item['metadata']
            })
        
        # Sort by similarity score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def delete(self, memory_id: Optional[str] = None, filter_metadata: Optional[Dict[str, Any]] = None, namespace: str = "general"):
        if memory_id:
            self.data = [item for item in self.data if item['id'] != memory_id]
        elif filter_metadata:
            new_data = []
            for item in self.data:
                match = True
                for k, v in filter_metadata.items():
                    if item['metadata'].get(k) != v:
                        match = False
                        break
                if not match:
                    new_data.append(item)
            self.data = new_data
        self._save_data()

# Initialize local DB client
vector_db_client = LocalVectorDB()

class LongTermMemory:
    """
    Manages the AI's persistent long-term memory using a local vector database.
    """

    def __init__(self, embedding_dimension: int = EMBEDDING_DIMENSION, default_namespace: str = "general"):
        """
        Initializes the LongTermMemory manager.
        """
        self.embedding_dimension = embedding_dimension
        self.default_namespace = default_namespace
        self._embedding_model = embedding_model
        self._vector_db = vector_db_client

        print(f"LongTermMemory initialized (Vector Dim: {embedding_dimension}, Default NS: '{default_namespace}')")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates a vector embedding for the given text.
        """
        if not text:
            print("Warning: Attempted to embed empty text.")
            return None
        try:
            if self._embedding_model:
                embedding = self._embedding_model.encode(text).tolist()
            else:
                # Fallback to random if no model is loaded (though we should have it in requirements)
                import random
                embedding = [random.random() for _ in range(self.embedding_dimension)]

            if len(embedding) != self.embedding_dimension:
                 print(f"Error: Embedding dimension mismatch. Expected {self.embedding_dimension}, got {len(embedding)}")
                 return None
            return embedding
        except Exception as e:
            print(f"Error generating embedding for text: {e}")
            return None

    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None, memory_id: Optional[str] = None, namespace: Optional[str] = None) -> Optional[str]:
        """
        Adds a piece of information (memory) to the long-term store.
        """
        if not content:
            print("Warning: Attempted to add memory with empty content.")
            return None

        embedding = self._get_embedding(content)
        if embedding is None:
            print("  - Failed to add memory due to embedding error.")
            return None

        memory_id = memory_id or str(uuid.uuid4())
        namespace = namespace or self.default_namespace
        timestamp = time.time()

        meta = metadata or {}
        meta['created_at'] = meta.get('created_at', timestamp)
        meta['content_preview'] = content[:100] + "..."

        try:
            self._vector_db.upsert(memory_id, embedding, meta, namespace)
            print(f"  - Successfully added/updated memory with ID: {memory_id}")
            return memory_id
        except Exception as e:
            print(f"Error adding memory to vector database: {e}")
            return None

    def retrieve_relevant_memories(self, query_content: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant memories based on semantic similarity.
        """
        query_embedding = self._get_embedding(query_content)
        if query_embedding is None:
            return []

        namespace = namespace or self.default_namespace

        try:
            relevant_memories = self._vector_db.query(query_embedding, top_k, namespace, filter_metadata)
            print(f"  - Found {len(relevant_memories)} relevant memories.")
            return relevant_memories
        except Exception as e:
            print(f"Error retrieving memories from vector database: {e}")
            return []

    def delete_memory(self, memory_id: Optional[str] = None, filter_metadata: Optional[Dict[str, Any]] = None, namespace: Optional[str] = None) -> bool:
        """
        Deletes memories based on ID or metadata filter.
        """
        if not memory_id and not filter_metadata:
            print("Error: Must provide either memory_id or filter_metadata to delete.")
            return False

        namespace = namespace or self.default_namespace
        try:
            self._vector_db.delete(memory_id, filter_metadata, namespace)
            return True
        except Exception as e:
            print(f"Error deleting memory from vector database: {e}")
            return False


    # Update might simply be delete + add with the same ID in many vector DBs
    # Add other methods as needed: list_namespaces, get_stats, update_metadata, etc.


# Example Usage (conceptual)
if __name__ == "__main__":
    # This part assumes placeholders are replaced with actual initialized clients
    print("\n--- Long Term Memory Example ---")

    # Ensure placeholder clients are minimally functional for example if needed
    # This is crude, replace with actual initialization
    if embedding_model is None:
        class MockEmbedding:
            def encode(self, text): return [random.random() for _ in range(384)]
        embedding_model = MockEmbedding()
        print("Initialized Mock Embedding Model for example.")
    if vector_db_client is None:
        class MockVectorDB:
            def upsert(self, vectors, namespace): print(f"Mock DB Upsert: {len(vectors)} vector(s) to NS '{namespace}'")
            def query(self, vector, top_k, include_metadata, namespace, filter):
                print(f"Mock DB Query: Top {top_k} in NS '{namespace}'")
                return {'matches': [{'id': str(uuid.uuid4()), 'score': random.random(), 'metadata': {'source':'mock'}} for _ in range(top_k)]}
            def delete(self, ids=None, filter=None, namespace=None): print(f"Mock DB Delete: IDs={ids}, Filter={filter}, NS='{namespace}'")
        vector_db_client = MockVectorDB()
        print("Initialized Mock Vector DB for example.")
        # Note: This mock DB setup is highly simplified and may not match real DB behavior.

    try:
        ltm = LongTermMemory(embedding_dimension=384)

        # Add memories
        id1 = ltm.add_memory("The user prefers concise summaries.", metadata={'type': 'preference', 'user_id': 'user123'})
        id2 = ltm.add_memory("Burp Suite is a tool for web application security testing.", metadata={'type': 'fact', 'source': 'documentation'})
        id3 = ltm.add_memory("Previous task involved scanning example.com.", metadata={'type': 'history', 'task_id': 'task_abc'})

        # Retrieve memories
        query = "What tool is used for web pentesting?"
        relevant = ltm.retrieve_relevant_memories(query, top_k=2)
        print(f"\nMemories relevant to '{query}':")
        for mem in relevant:
            print(f"  - ID: {mem.get('id')}, Score: {mem.get('score'):.4f}, Meta: {mem.get('metadata')}")

        query2 = "What did the user ask for last time?"
        relevant2 = ltm.retrieve_relevant_memories(query2, top_k=2, filter_metadata={'type': 'history'}) # Example filter
        print(f"\nMemories relevant to '{query2}' (filtered by history):")
        for mem in relevant2:
            print(f"  - ID: {mem.get('id')}, Score: {mem.get('score'):.4f}, Meta: {mem.get('metadata')}")

        # Delete a memory
        if id1:
            print(f"\nAttempting to delete memory: {id1}")
            deleted = ltm.delete_memory(memory_id=id1)
            print(f"Deletion attempted: {deleted}")

    except ValueError as ve:
        print(f"\nSkipping example usage due to configuration error: {ve}")
    except Exception as e:
         print(f"\nAn error occurred during example usage: {e}")


    print("--- End Example ---")
