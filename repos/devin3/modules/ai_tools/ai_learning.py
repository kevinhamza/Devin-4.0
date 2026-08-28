# Devin/modules/ai_tools/ai_learning.py
# Purpose: A long-term memory and learning system for Devin using a vector
#          database for Retrieval-Augmented Generation (RAG).

import logging
import os
import uuid
from typing import List, Dict, Optional, Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("AILearning")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class AILearning:
    """
    Manages a long-term, semantic memory for Devin using a vector store.
    """
    def __init__(self, db_path: str = "./devin_memory", collection_name: str = "knowledge_base"):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required for the learning module. 'pip install chromadb sentence-transformers'")

        logger.info(f"Initializing vector memory at path: {db_path}")
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Use a persistent client to save data to disk
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Use a pre-built sentence transformer model for embedding
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
        logger.info(f"Memory collection '{self.collection_name}' loaded/created.")

    def add_memory(self, content: str, metadata: Dict[str, Any]):
        """
        Adds a new piece of information (a memory) to the vector store.

        Args:
            content (str): The text content of the memory.
            metadata (Dict[str, Any]): A dictionary of metadata (e.g., type, target, timestamp).
        """
        if not isinstance(metadata, dict):
            raise TypeError("Metadata must be a dictionary.")
        if not content.strip():
            logger.warning("Attempted to add an empty memory. Skipping.")
            return

        memory_id = str(uuid.uuid4())
        logger.info(f"Adding new memory (ID: {memory_id}): '{content[:50]}...'")
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )
        except Exception as e:
            logger.error(f"Failed to add memory to ChromaDB: {e}")

    def retrieve_memories(self, query: str, n_results: int = 3, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant memories based on a query.

        Args:
            query (str): The query to search for relevant memories.
            n_results (int): The maximum number of memories to return.
            filter_metadata (Optional[Dict]): A dictionary to filter memories by metadata.

        Returns:
            A list of dictionaries, where each dictionary contains the memory's content and metadata.
        """
        logger.info(f"Retrieving {n_results} memories for query: '{query}'")
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Unpack the results into a more usable format
            retrieved = []
            if results and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    retrieved.append({
                        "id": doc_id,
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i]
                    })
            return retrieved
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            return []
            
# --- Example Usage ---
if __name__ == "__main__":
    import shutil
    
    print("=========================================================")
    print("=== AI Learning & Memory Prototype (RAG) 🧠📚 ===")
    print("=========================================================")
    
    if not CHROMADB_AVAILABLE:
        print("ERROR: This demo requires 'chromadb' and 'sentence-transformers'. Please install them.")
    else:
        memory_path = "./devin_memory_demo"
        # Clean up previous demo run if it exists
        if os.path.exists(memory_path):
            shutil.rmtree(memory_path)
            
        try:
            # 1. Initialize the learning module
            learner = AILearning(db_path=memory_path)
            
            # 2. Add some sample memories, simulating past tool runs
            print("\n--- Adding Sample Memories ---")
            learner.add_memory(
                content="Port scan on 'db-server-01' (10.0.5.20) found port 3306 (MySQL) to be open.",
                metadata={"type": "scan_result", "tool": "network_scanner", "target": "10.0.5.20"}
            )
            learner.add_memory(
                content="Anonymous FTP login is enabled on the server at 192.168.1.150. This allowed access to the /pub/ directory.",
                metadata={"type": "vulnerability", "tool": "vulnerability_scanner", "target": "192.168.1.150"}
            )
            learner.add_memory(
                content="Subdomain enumeration for 'corp.com' found 'dev.corp.com' and 'api.corp.com'.",
                metadata={"type": "discovery_result", "tool": "subdomain_enum", "target": "corp.com"}
            )
            
            # 3. Retrieve memories based on new user queries
            print("\n\n--- Retrieving Memories Based on New Queries ---")
            
            # Query 1: A question about databases
            query1 = "what can we do to the database server?"
            retrieved1 = learner.retrieve_memories(query1)
            print(f"\nQuery: '{query1}'")
            print("Retrieved Memories:")
            for mem in retrieved1:
                print(f"  - (Relevance: {1-mem['distance']:.2f}) {mem['content']}")
                
            # Query 2: A question about a specific host
            query2 = "what did we find on the metasploitable machine?"
            retrieved2 = learner.retrieve_memories(query2, filter_metadata={"target": "192.168.1.150"})
            print(f"\nQuery: '{query2}' (filtered for target)")
            print("Retrieved Memories:")
            for mem in retrieved2:
                print(f"  - (Relevance: {1-mem['distance']:.2f}) {mem['content']}")

        finally:
            # 4. Clean up the demo database directory
            if os.path.exists(memory_path):
                shutil.rmtree(memory_path)
                logger.info(f"Cleaned up demo memory directory: {memory_path}")


    print("\n=========================================================")
    print("=== AI Learning Prototype Complete ===")
    print("=========================================================")
