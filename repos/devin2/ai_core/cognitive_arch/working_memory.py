# Devin/ai_core/cognitive_arch/working_memory.py

import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

class WorkingMemory:
    """
    Manages the AI's short-term working memory.

    Holds temporary information, recent interactions, intermediate results,
    and contextual data relevant to the current task or reasoning process.
    Designed to provide quick access to context for the Reasoning Engine.
    """

    def __init__(self, max_size: int = 100, retention_strategy: str = 'fifo'):
        """
        Initializes the working memory.

        Args:
            max_size (int): Maximum number of items or tokens to hold.
            retention_strategy (str): How to handle exceeding max_size ('fifo', 'lru', etc.).
                                      (Implementation of strategies beyond fifo not shown here).
        """
        self.max_size = max_size
        self.retention_strategy = retention_strategy
        # Using deque for efficient additions/removals from both ends (useful for FIFO)
        self._memory: deque[Tuple[float, str, Any]] = deque(maxlen=max_size) # Stores (timestamp, key, value)
        self._keyed_memory: Dict[str, Any] = {} # Allows direct access by key
        print(f"WorkingMemory initialized (max_size={max_size}, strategy='{retention_strategy}')")

    def add_item(self, key: str, value: Any, importance: float = 0.5):
        """
        Adds or updates an item in the working memory.

        Args:
            key (str): A unique identifier for the memory item.
            value (Any): The data to store.
            importance (float): Optional measure of item importance (not fully utilized in this skeleton).
        """
        timestamp = time.time()
        print(f"Adding/Updating item in Working Memory: Key='{key}'")

        # Remove old entry if key exists to avoid duplicate keys in deque
        # This implementation is simple; more complex handling might be needed
        if key in self._keyed_memory:
            self._memory = deque([(ts, k, v) for ts, k, v in self._memory if k != key], maxlen=self.max_size)

        # Add new item
        memory_tuple = (timestamp, key, value)
        self._memory.append(memory_tuple)
        self._keyed_memory[key] = value

        # Ensure max_size constraint (deque handles this automatically for the sequence)
        # We also need to remove from keyed_memory if deque evicted an item
        if len(self._memory) == self.max_size and self.max_size > 0:
             # If deque is full and we added, the oldest item was automatically removed
             # We need to find which item was removed and delete it from _keyed_memory
             current_keys = {k for _, k, _ in self._memory}
             removed_keys = set(self._keyed_memory.keys()) - current_keys
             for removed_key in removed_keys:
                 print(f"  - Item evicted due to size limit: Key='{removed_key}'")
                 del self._keyed_memory[removed_key]


    def get_item(self, key: str) -> Optional[Any]:
        """
        Retrieves an item by its key.

        Args:
            key (str): The key of the item to retrieve.

        Returns:
            Optional[Any]: The value associated with the key, or None if not found.
        """
        print(f"Attempting to retrieve item from Working Memory: Key='{key}'")
        return self._keyed_memory.get(key)

    def get_recent_items(self, count: int = 5) -> List[Tuple[float, str, Any]]:
        """
        Retrieves the most recently added items.

        Args:
            count (int): The maximum number of recent items to return.

        Returns:
            List[Tuple[float, str, Any]]: A list of the most recent items (timestamp, key, value).
        """
        print(f"Retrieving recent {count} items from Working Memory.")
        # Deque stores items in insertion order, so the end of the deque is the most recent
        return list(self._memory)[-count:]

    def get_all_items(self) -> List[Tuple[float, str, Any]]:
        """
        Retrieves all items currently in working memory.

        Returns:
            List[Tuple[float, str, Any]]: A list of all items (timestamp, key, value).
        """
        print("Retrieving all items from Working Memory.")
        return list(self._memory)

    def search_items(self, query: str) -> List[Tuple[float, str, Any]]:
        """
        Performs a simple keyword search within the memory (keys and values if strings).
        NOTE: This is a basic placeholder. Real implementation might use embeddings or more sophisticated search.

        Args:
            query (str): The search term.

        Returns:
            List[Tuple[float, str, Any]]: A list of matching items.
        """
        print(f"Searching Working Memory for query: '{query}'")
        results = []
        query_lower = query.lower()
        for item_tuple in self._memory:
            ts, key, value = item_tuple
            match = False
            if query_lower in key.lower():
                match = True
            if isinstance(value, str) and query_lower in value.lower():
                match = True
            # Add more sophisticated matching logic here if needed

            if match:
                results.append(item_tuple)
        print(f"  - Found {len(results)} potential matches.")
        return results

    def clear_memory(self):
        """
        Clears all items from the working memory.
        """
        print("Clearing Working Memory.")
        self._memory.clear()
        self._keyed_memory.clear()

    def get_current_size(self) -> int:
        """Returns the number of items currently in memory."""
        return len(self._memory)

    def __str__(self) -> str:
        """String representation of the working memory."""
        return f"WorkingMemory(size={self.get_current_size()}, max_size={self.max_size})"

# Example Usage (conceptual)
if __name__ == "__main__":
    # This part would typically not be in the module file itself
    # It's here just for concept demonstration.
    print("\n--- Working Memory Example ---")
    memory = WorkingMemory(max_size=3)
    memory.add_item("user_request", "Find vulnerabilities in example.com")
    memory.add_item("current_step", "Subdomain enumeration")
    print(memory)
    memory.add_item("tool_used", "subfinder")
    print(memory)
    memory.add_item("subdomains_found", ["api.example.com", "dev.example.com"]) # This will evict user_request
    print(memory)
    print("Recent items:", memory.get_recent_items(2))
    print("Subdomains:", memory.get_item("subdomains_found"))
    print("User Request:", memory.get_item("user_request")) # Should be None now
    memory.clear_memory()
    print(memory)
    print("--- End Example ---")
