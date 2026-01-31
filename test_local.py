import os
import json
import argparse
from cryptography.fernet import Fernet

# Setup local env keys
if "ENCRYPTION_KEY" not in os.environ:
    os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()

# Use models folder
if "MODELS" not in os.environ:
    # Small default for testing
    os.environ["MODELS"] = "Qwen/Qwen2.5-0.5B-Instruct-GGUF:qwen2.5-0.5b-instruct-q4_k_m.gguf"

from rp_handler import handler

def run_test(prompt):
    print(f"--- 🛠️  Local Test (Key: {os.environ['ENCRYPTION_KEY']}) ---")
    
    # 1. Encrypt
    f = Fernet(os.environ["ENCRYPTION_KEY"].encode())
    payload = {"prompt": prompt, "sampling_params": {"max_tokens": 100}}
    encrypted = f.encrypt(json.dumps(payload).encode()).decode()

    # 2. Mock Job
    job = {"input": {"encrypted_input": encrypted}}

    print(f"Prompt: {prompt}")
    print("Response: ", end="")
    
    # 3. Run Handler
    for chunk in handler(job):
        if isinstance(chunk, dict) and "error" in chunk:
            print(f"\n[ERROR] {chunk['error']}")
        else:
            print(chunk, end="", flush=True)
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="Explain the benefit of llama.cpp vs vllm.")
    args = parser.parse_args()
    run_test(args.prompt)
