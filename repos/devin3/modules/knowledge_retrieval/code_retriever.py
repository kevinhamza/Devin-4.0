# Devin/modules/knowledge_retrieval/code_retriever.py
# Purpose: An intelligent engine for indexing, searching, and retrieving
#          code from a project directory, using both keyword and semantic search.

import logging
import os
import ast
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("CodeRetriever")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

@dataclass
class CodeBlock:
    """Represents an indexed block of code (a class or function)."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    block_type: str # 'class' or 'function'
    source_code: str
    docstring: Optional[str] = None

class CodeRetriever:
    """
    Indexes a codebase and provides powerful search and retrieval capabilities.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.index: Dict[str, CodeBlock] = {}
        
        # For semantic search
        self.semantic_model = None
        self.semantic_vectors = None
        self.semantic_index_map: List[str] = []

        logger.info(f"Initializing CodeRetriever for project at '{self.project_root}'")
        self._build_index()
        
        if SEMANTIC_AVAILABLE:
            logger.info("Semantic search dependencies found. Building semantic index...")
            self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            self._build_semantic_index()
        else:
            logger.warning("`sentence-transformers` or `numpy` not found. Semantic search will be disabled.")

    def _build_index(self):
        """Walks the project directory and uses AST to index all code blocks."""
        logger.info("Building code index...")
        for py_file in self.project_root.rglob("*.py"):
            try:
                relative_path = str(py_file.relative_to(self.project_root))
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        block_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                        full_name = f"{relative_path}::{node.name}"
                        source_segment = ast.get_source_segment(content, node)
                        
                        self.index[full_name] = CodeBlock(
                            name=node.name,
                            file_path=relative_path,
                            start_line=node.lineno,
                            end_line=node.end_lineno,
                            block_type=block_type,
                            source_code=source_segment,
                            docstring=ast.get_docstring(node)
                        )
            except Exception as e:
                logger.error(f"Failed to parse or index {py_file}: {e}")
        logger.info(f"Code index built. Found {len(self.index)} functions and classes.")

    def _build_semantic_index(self):
        """Creates vector embeddings for all indexed code blocks."""
        docs_to_embed = []
        for key, block in self.index.items():
            # Use docstring if available, otherwise use the code itself as context
            content = block.docstring if block.docstring else block.name
            docs_to_embed.append(content)
            self.semantic_index_map.append(key)
        
        if docs_to_embed:
            self.semantic_vectors = self.semantic_model.encode(docs_to_embed, show_progress_bar=True)
            logger.info(f"Semantic index built. Created {self.semantic_vectors.shape[0]} vectors.")

    def get_code_block(self, full_name: str) -> Optional[str]:
        """Retrieves the full source code of a specific class or function."""
        block = self.index.get(full_name)
        return block.source_code if block else None

    def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Performs a simple text search across the codebase."""
        results = []
        for key, block in self.index.items():
            if keyword.lower() in block.source_code.lower():
                results.append({"name": key, "file_path": block.file_path, "line": block.start_line})
        return results

    def search_semantically(self, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Finds code blocks that are semantically related to a natural language query."""
        if not SEMANTIC_AVAILABLE or self.semantic_vectors is None:
            logger.error("Semantic search is not available.")
            return None
        
        query_vector = self.semantic_model.encode(query)
        
        # Calculate cosine similarity
        similarities = np.dot(self.semantic_vectors, query_vector) / (np.linalg.norm(self.semantic_vectors, axis=1) * np.linalg.norm(query_vector))
        
        # Get the top_k results
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_k_indices:
            key = self.semantic_index_map[idx]
            block = self.index[key]
            results.append({
                "name": key,
                "file_path": block.file_path,
                "similarity": float(similarities[idx]),
                "summary": block.docstring or block.name
            })
        return results

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Code Retriever & Semantic Search Demo 🧠💻 ===")
    print("=========================================================")
    
    try:
        # Initialize the retriever on its own project directory
        retriever = CodeRetriever(project_root=".")
        
        # --- 1. Demonstrate Direct Retrieval ---
        print("\n--- 1. Retrieving a specific function: ToolExecutor.execute_tool ---")
        # Note: The path separator might be different on Windows (\).
        tool_executor_path = os.path.join("modules", "tool_executor.py")
        code = retriever.get_code_block(f"{tool_executor_path}::execute_tool")
        if code:
            print("```python\n" + "\n".join(code.splitlines()[:5]) + "\n  ...\n```")
        else:
            print("  Function not found in index.")
            
        # --- 2. Demonstrate Keyword Search ---
        print("\n--- 2. Keyword search for 'websocket' ---")
        results = retriever.search_by_keyword("websocket")
        for res in results[:3]: # Show first 3 results
            print(f"  - Found in: {res['name']} (Line: {res['line']})")
        
        # --- 3. Demonstrate Semantic Search ---
        if SEMANTIC_AVAILABLE:
            print("\n--- 3. Semantic search for 'How to check for dangerous commands?' ---")
            semantic_results = retriever.search_semantically("How to check for dangerous commands?")
            if semantic_results:
                for res in semantic_results:
                    print(f"  - Found: {res['name']} (Similarity: {res['similarity']:.2f})")
                    print(f"    -> Summary: {res['summary']}")
        else:
            print("\n--- 3. Semantic search is disabled (dependencies not installed) ---")

    except Exception as e:
        logger.error(f"Demo failed to run: {e}", exc_info=True)
        if not SEMANTIC_AVAILABLE:
            print("\nNOTE: To enable semantic search, run: pip install sentence-transformers numpy")

    print("\n=========================================================")
    print("=== Code Retriever Demo Complete ===")
    print("=========================================================")
