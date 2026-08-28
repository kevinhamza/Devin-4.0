# scripts/model_updater.py
from huggingface_hub import hf_hub_download
from pathlib import Path

# A conceptual list of models Devin might use from HuggingFace
MODELS_TO_UPDATE = [
    {
        "repo_id": "sentence-transformers/all-MiniLM-L6-v2",
        "filename": "pytorch_model.bin",
    },
    {
        "repo_id": "distilbert-base-uncased-finetuned-sst-2-english",
        "filename": "config.json"
    }
]

MODEL_DIR = Path("./models")
MODEL_DIR.mkdir(exist_ok=True)

def update_models():
    print("--- Checking for AI model updates from HuggingFace Hub ---")
    for model in MODELS_TO_UPDATE:
        print(f"  Checking model: {model['repo_id']}")
        try:
            downloaded_path = hf_hub_download(
                repo_id=model['repo_id'],
                filename=model['filename'],
                local_dir=MODEL_DIR / model['repo_id'],
                local_dir_use_symlinks=False # For cross-platform compatibility
            )
            print(f"    -> Model file is up to date at: {downloaded_path}")
        except Exception as e:
            print(f"    -> ERROR: Could not download model '{model['repo_id']}': {e}")
            
    print("\n--- Model update check complete ---")

if __name__ == "__main__":
    update_models()
