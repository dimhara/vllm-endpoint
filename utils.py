import os
import sys

# CRITICAL: Set this BEFORE importing huggingface_hub to ensure it picks up the Rust downloader
if "HF_HUB_ENABLE_HF_TRANSFER" not in os.environ:
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from huggingface_hub import snapshot_download, constants

# Defined in RunPod docs
RUNPOD_CACHE_DIR = "/runpod-volume/huggingface-cache/hub"

def get_model_map():
    """
    Parses the MODELS environment variable.
    Format: repo_id,repo_id
    """
    models_env = os.environ.get("MODELS", "")
    if not models_env:
        return []
    return [entry.strip() for entry in models_env.split(",") if entry.strip()]

def resolve_model(repo_id, download_dir):
    """
    Downloads the full model snapshot using hf_transfer (Rust).
    """
    print(f"[Download] Checking/Downloading {repo_id} to {download_dir}...")
    
    try:
        # snapshot_download automatically uses hf_transfer if the env var is set
        # and the package is installed.
        path = snapshot_download(
            repo_id=repo_id,
            cache_dir=download_dir,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite"], # Optimization: Skip non-vLLM weights
            local_dir_use_symlinks=True # Optimization: Use symlinks if possible to save space
        )
        print(f"[Ready] Model available at: {path}")
        return path
    except Exception as e:
        print(f"Error downloading {repo_id}: {e}")
        raise e

def prepare_models(target_dir):
    """
    Iterates through env vars and ensures all models are ready.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    model_list = get_model_map()
    first_model_path = None

    print(f"--- Resolving {len(model_list)} models (HF_TRANSFER={'Enabled' if os.environ.get('HF_HUB_ENABLE_HF_TRANSFER') == '1' else 'Disabled'}) ---")

    for i, repo_id in enumerate(model_list):
        path = resolve_model(repo_id, target_dir)
        if i == 0:
            first_model_path = path
        
    return first_model_path

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/models"
    prepare_models(target)
