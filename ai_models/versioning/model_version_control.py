# Devin/ai_models/versioning/model_version_control.py # Git-like model versioning

import os
import json
import hashlib
import datetime
import shutil
import threading
from typing import Dict, Any, List, Optional, TypedDict

# --- Data Structure for Version Metadata ---

class ModelVersionInfo(TypedDict):
    """Structure to hold metadata for a single registered model version."""
    version_id: str         # Unique identifier (e.g., hash)
    model_name: str         # Name of the model (e.g., "text-summarizer", "object-detector")
    timestamp: str          # ISO format timestamp of registration
    model_path: str         # Path to the actual model file (e.g., on disk, S3 URL)
    # --- Optional Lineage & Provenance ---
    parent_version_id: Optional[str] # ID of the version this was based on/fine-tuned from
    source_code_version: Optional[str] # Git commit hash of the training code
    training_dataset_ref: Optional[str] # Reference to the dataset version used
    training_parameters: Optional[Dict[str, Any]] # Hyperparameters, config used
    # --- Optional Performance & Artifacts ---
    validation_metrics: Optional[Dict[str, float]] # Key performance metrics (e.g., accuracy, F1)
    related_artifacts: Optional[Dict[str, str]] # Paths to related files (tokenizer, config)
    description: Optional[str]    # User-provided description or comments


class ModelVersionControl:
    """
    Manages versioning of AI model metadata, inspired by Git concepts.

    Tracks model lineage, parameters, metrics, and file locations.
    Does NOT store large model files directly in its registry; stores paths instead.
    """
    # Class variable for default storage path (can be overridden)
    DEFAULT_REGISTRY_PATH = "./ai_models/registry/model_registry.json"
    DEFAULT_MODEL_STORAGE_DIR = "./ai_models/storage/" # Dir to copy registered models

    def __init__(self, registry_file_path: Optional[str] = None, model_storage_dir: Optional[str] = None):
        """
        Initializes the Model Version Control system.

        Args:
            registry_file_path (Optional[str]): Path to the JSON file used as the registry.
                                                Defaults to DEFAULT_REGISTRY_PATH.
            model_storage_dir (Optional[str]): Directory where registered model files should be
                                               copied for versioning. Defaults to DEFAULT_MODEL_STORAGE_DIR.
                                               Set to None to disable automatic copying.
        """
        self.registry_path = registry_file_path or self.DEFAULT_REGISTRY_PATH
        self.storage_dir = model_storage_dir or self.DEFAULT_MODEL_STORAGE_DIR
        self._registry: Dict[str, List[ModelVersionInfo]] = {} # {model_name: [version_info, ...]}
        self._tags: Dict[str, Dict[str, str]] = {} # {model_name: {tag_name: version_id, ...}}
        self._lock = threading.Lock() # Ensure thread safety for registry access

        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        if self.storage_dir:
            os.makedirs(self.storage_dir, exist_ok=True)

        self._load_registry()
        print(f"ModelVersionControl initialized. Registry: '{self.registry_path}', Storage: '{self.storage_dir or 'Disabled'}'")

    def _load_registry(self):
        """Loads the registry state from the JSON file."""
        with self._lock:
            if os.path.exists(self.registry_path):
                try:
                    with open(self.registry_path, 'r') as f:
                        data = json.load(f)
                        self._registry = data.get('registry', {})
                        self._tags = data.get('tags', {})
                        print(f"  - Loaded registry with {len(self._registry)} models and tags.")
                except (json.JSONDecodeError, IOError) as e:
                    print(f"  - Warning: Could not load registry file '{self.registry_path}': {e}. Starting fresh.")
                    self._registry = {}
                    self._tags = {}
            else:
                print("  - No existing registry file found. Starting fresh.")
                self._registry = {}
                self._tags = {}

    def _save_registry(self):
        """Saves the current registry state to the JSON file."""
        with self._lock:
            try:
                with open(self.registry_path, 'w') as f:
                    json.dump({'registry': self._registry, 'tags': self._tags}, f, indent=2)
                # print("  - Registry saved.") # Can be verbose
            except IOError as e:
                print(f"  - Error saving registry file '{self.registry_path}': {e}")

    def _generate_version_id(self, model_name: str, model_path: str, timestamp: str) -> str:
        """Generates a unique version ID (conceptual hash)."""
        # Simple hash based on name, path basename, and time.
        # Could also hash file content for more robustness (but slower).
        hasher = hashlib.sha1()
        hasher.update(model_name.encode())
        hasher.update(os.path.basename(model_path).encode())
        hasher.update(timestamp.encode())
        return hasher.hexdigest()[:12] # Short hash like Git

    def register_version(self,
                         model_name: str,
                         model_file_path: str, # Path to the candidate model file
                         training_params: Optional[Dict] = None,
                         validation_metrics: Optional[Dict] = None,
                         source_code_version: Optional[str] = None,
                         training_dataset_ref: Optional[str] = None,
                         parent_version_id: Optional[str] = None,
                         description: Optional[str] = None,
                         related_artifacts: Optional[Dict] = None
                         ) -> Optional[ModelVersionInfo]:
        """
        Registers a new version of a model. Conceptually similar to 'git commit'.

        Copies the model file to the versioned storage directory if configured.

        Args:
            model_name (str): Name of the model.
            model_file_path (str): Path to the model file being registered.
            training_params (Optional[Dict]): Parameters used for training.
            validation_metrics (Optional[Dict]): Performance metrics.
            source_code_version (Optional[str]): Git hash of training code.
            training_dataset_ref (Optional[str]): Reference to dataset used.
            parent_version_id (Optional[str]): Previous version ID if applicable.
            description (Optional[str]): Description of this version.
            related_artifacts (Optional[Dict]): Dict mapping artifact name to its path.

        Returns:
            Optional[ModelVersionInfo]: Metadata of the newly registered version, or None on failure.
        """
        print(f"\nRegistering new version for model '{model_name}'...")
        if not os.path.exists(model_file_path):
            print(f"  - Error: Model file not found at '{model_file_path}'")
            return None

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        version_id = self._generate_version_id(model_name, model_file_path, timestamp)
        print(f"  - Generated Version ID: {version_id}")

        versioned_model_path = model_file_path # Default to original path
        # Copy model to versioned storage if enabled
        if self.storage_dir:
            try:
                model_filename = os.path.basename(model_file_path)
                versioned_dir = os.path.join(self.storage_dir, model_name, version_id)
                os.makedirs(versioned_dir, exist_ok=True)
                versioned_model_path = os.path.join(versioned_dir, model_filename)
                shutil.copy2(model_file_path, versioned_model_path) # copy2 preserves metadata
                print(f"  - Copied model file to versioned storage: '{versioned_model_path}'")

                # Copy related artifacts if provided
                if related_artifacts:
                    for name, path in related_artifacts.items():
                         if os.path.exists(path):
                              artifact_filename = os.path.basename(path)
                              dest_path = os.path.join(versioned_dir, artifact_filename)
                              shutil.copy2(path, dest_path)
                              # Update artifact path to be relative to storage? Or store absolute? Storing absolute for now.
                              # related_artifacts[name] = dest_path # If you want path within storage
                              print(f"    - Copied artifact '{name}' to '{dest_path}'")
                         else:
                              print(f"    - Warning: Artifact '{name}' path not found: '{path}'")

            except (IOError, OSError) as e:
                print(f"  - Error copying model/artifacts to storage '{self.storage_dir}': {e}")
                # Decide if registration should fail if copy fails - let's allow it for now
                versioned_model_path = model_file_path # Fallback to original path if copy failed

        # Create metadata entry
        version_info: ModelVersionInfo = {
            "version_id": version_id,
            "model_name": model_name,
            "timestamp": timestamp,
            "model_path": versioned_model_path, # Path in storage or original path
            "parent_version_id": parent_version_id,
            "source_code_version": source_code_version,
            "training_dataset_ref": training_dataset_ref,
            "training_parameters": training_params,
            "validation_metrics": validation_metrics,
            "related_artifacts": related_artifacts or {}, # Store paths to copied artifacts if any
            "description": description or f"Registered on {timestamp}"
        }

        # Add to registry (thread-safe)
        with self._lock:
            if model_name not in self._registry:
                self._registry[model_name] = []
            # Prevent duplicate registration if ID somehow collided (unlikely with timestamp)
            if any(v['version_id'] == version_id for v in self._registry[model_name]):
                 print(f"  - Error: Version ID {version_id} collision. Registration failed.")
                 # Cleanup copied files? Maybe not if collision is rare.
                 return None
            self._registry[model_name].append(version_info)
            print(f"  - Registered version {version_id} for model '{model_name}'.")

        self._save_registry() # Save after successful registration
        return version_info

    def get_version_info(self, model_name: str, version_ref: str) -> Optional[ModelVersionInfo]:
        """
        Gets the metadata for a specific model version, identified by ID or tag.

        Args:
            model_name (str): The name of the model.
            version_ref (str): The version ID or a tag name (e.g., "production", "latest").

        Returns:
            Optional[ModelVersionInfo]: The metadata dictionary, or None if not found.
        """
        with self._lock: # Lock needed for reading tags and registry potentially
            version_id = version_ref
            # Check if the reference is a tag
            if model_name in self._tags and version_ref in self._tags[model_name]:
                version_id = self._tags[model_name][version_ref]
                print(f"  - Resolved tag '{version_ref}' to version_id '{version_id}' for model '{model_name}'.")

            # Find the version by ID
            if model_name in self._registry:
                 for version_info in self._registry[model_name]:
                     if version_info['version_id'] == version_id:
                         return version_info

        print(f"  - Version reference '{version_ref}' (resolved to ID '{version_id}') not found for model '{model_name}'.")
        return None

    def list_versions(self, model_name: str) -> List[ModelVersionInfo]:
        """Lists all registered versions for a given model, newest first. Conceptually like 'git log'."""
        with self._lock:
            versions = self._registry.get(model_name, [])
            # Sort by timestamp descending
            return sorted(versions, key=lambda v: v['timestamp'], reverse=True)

    def tag_version(self, model_name: str, version_id: str, tag_name: str) -> bool:
        """
        Assigns a tag (e.g., "production", "staging") to a specific version ID.
        Conceptually like 'git tag'. Overwrites existing tag if present.

        Args:
            model_name (str): The name of the model.
            version_id (str): The version ID to tag.
            tag_name (str): The name of the tag.

        Returns:
            bool: True if tagging was successful, False otherwise (e.g., version_id not found).
        """
        print(f"Attempting to tag version '{version_id}' of model '{model_name}' as '{tag_name}'...")
        with self._lock:
            # Check if version exists
            version_exists = False
            if model_name in self._registry:
                 if any(v['version_id'] == version_id for v in self._registry[model_name]):
                      version_exists = True

            if not version_exists:
                 print(f"  - Error: Version ID '{version_id}' not found for model '{model_name}'. Cannot tag.")
                 return False

            # Create tag
            if model_name not in self._tags:
                self._tags[model_name] = {}
            self._tags[model_name][tag_name] = version_id
            print(f"  - Successfully tagged version '{version_id}' as '{tag_name}'.")

        self._save_registry()
        return True

    def get_model_path(self, model_name: str, version_ref: str) -> Optional[str]:
        """
        Gets the stored file path for a specific model version or tag.

        Args:
            model_name (str): The name of the model.
            version_ref (str): The version ID or a tag name.

        Returns:
            Optional[str]: The file path, or None if the version/tag is not found.
        """
        version_info = self.get_version_info(model_name, version_ref)
        if version_info:
            path = version_info.get('model_path')
            if path and os.path.exists(path): # Optionally check if path still exists
                 return path
            elif path:
                 print(f"  - Warning: Path '{path}' for version '{version_ref}' not found on disk.")
                 return path # Return path anyway, let caller handle non-existence
            else:
                 print(f"  - Error: No model path found in metadata for version '{version_ref}'.")
                 return None
        return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Model Version Control Example ---")

    # Use temporary files/dirs for example
    registry_file = "./temp_model_registry.json"
    storage_dir = "./temp_model_storage/"
    # Clean up previous example runs if they exist
    if os.path.exists(registry_file): os.remove(registry_file)
    if os.path.exists(storage_dir): shutil.rmtree(storage_dir)

    mvc = ModelVersionControl(registry_file_path=registry_file, model_storage_dir=storage_dir)

    # Simulate creating some dummy model files
    model_name = "sentiment_analyzer"
    os.makedirs(f"./temp_models/{model_name}", exist_ok=True)
    model_v1_path = f"./temp_models/{model_name}/sentiment_v1.pkl"
    model_v2_path = f"./temp_models/{model_name}/sentiment_v2.onnx"
    tokenizer_path = f"./temp_models/{model_name}/tokenizer.json"
    with open(model_v1_path, "w") as f: f.write("dummy model v1 content")
    with open(model_v2_path, "w") as f: f.write("dummy model v2 content - different format")
    with open(tokenizer_path, "w") as f: f.write('{"config": "dummy tokenizer"}')

    # Register V1
    v1_info = mvc.register_version(
        model_name=model_name,
        model_file_path=model_v1_path,
        training_params={"lr": 0.001, "epochs": 5},
        validation_metrics={"accuracy": 0.85, "f1": 0.83},
        source_code_version="git_hash_1",
        training_dataset_ref="dataset_v1.0",
        description="Initial baseline model.",
        related_artifacts={"tokenizer": tokenizer_path}
    )
    time.sleep(0.1) # Ensure different timestamp for next version

    # Register V2
    v2_info = mvc.register_version(
        model_name=model_name,
        model_file_path=model_v2_path,
        training_params={"lr": 0.0005, "epochs": 10, "augmentation": True},
        validation_metrics={"accuracy": 0.91, "f1": 0.90},
        source_code_version="git_hash_2",
        training_dataset_ref="dataset_v1.1_augmented",
        parent_version_id=v1_info['version_id'] if v1_info else None,
        description="Improved model with more epochs and data augmentation. ONNX format.",
        related_artifacts={"tokenizer": tokenizer_path} # Same tokenizer
    )

    if v1_info and v2_info:
        # List versions
        print("\nListing Versions:")
        versions = mvc.list_versions(model_name)
        for v in versions:
            print(f"- ID: {v['version_id']}, Time: {v['timestamp']}, Metrics: {v.get('validation_metrics')}, Path: {v.get('model_path')}")

        # Tag versions
        print("\nTagging Versions:")
        mvc.tag_version(model_name, v1_info['version_id'], "baseline")
        mvc.tag_version(model_name, v2_info['version_id'], "latest")
        mvc.tag_version(model_name, v2_info['version_id'], "production") # Overwrite latest with production

        # Get specific version info by tag
        print("\nGetting 'production' version info:")
        prod_info = mvc.get_version_info(model_name, "production")
        if prod_info:
             print(json.dumps(prod_info, indent=2))

        # Get model path by tag
        print("\nGetting 'production' model path:")
        prod_path = mvc.get_model_path(model_name, "production")
        if prod_path:
             print(f"  Path: {prod_path}")
             # Check if file exists in storage
             print(f"  Exists in storage? {os.path.exists(prod_path)}")


    # Clean up temporary files
    # print("\nCleaning up temporary files/dirs...")
    # if os.path.exists(registry_file): os.remove(registry_file)
    # if os.path.exists(storage_dir): shutil.rmtree(storage_dir)
    # if os.path.exists("./temp_models"): shutil.rmtree("./temp_models")

    print("\n--- End Example ---")
