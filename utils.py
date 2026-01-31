import os
import sys
from huggingface_hub import hf_hub_download

# Enable fast Rust-based downloader
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

def prepare_models(target_dir):
    """
    Expects MODELS env in format 'repo_id:filename'
    Example: 'Qwen/Qwen2.5-7B-Instruct-GGUF:qwen2.5-7b-instruct-q4_k_m.gguf'
    """
    model_env = os.environ.get("MODELS", "")
    
    if not model_env:
        print("❌ Error: MODELS environment variable is empty.")
        sys.exit(1)
        
    if ":" not in model_env:
        print("❌ Error: MODELS must be in format 'repo_id:filename'")
        sys.exit(1)
    
    repo_id, filename = model_env.split(":", 1)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print(f"--- 📥 Downloading GGUF: {filename} from {repo_id} ---")
    
    # hf_hub_download will check the cache directory first automatically
    path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=target_dir,
        local_dir_use_symlinks=False
    )
    
    print(f"--- ✅ Model ready at: {path} ---")
    return path

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/models"
    prepare_models(target)
