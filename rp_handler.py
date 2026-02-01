import os
import runpod
import json
import traceback
from cryptography.fernet import Fernet
from llama_cpp import Llama
import utils

# CONFIG
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
ENABLE_FLASH_ATTN = os.environ.get("ENABLE_FLASH_ATTN", "false").lower() == "true"

llm = None

def init_engine():
    global llm
    if llm is not None: return

    print("--- 🚀 Initializing llama.cpp Secure Worker ---")
    
    model_dir = os.environ.get("MODEL_DIR", "/models")
    # Keep auto-detect by defaulting to None if env var is empty
    requested_format = os.environ.get("CHAT_FORMAT") 
    if not requested_format:
        requested_format = None

    try:
        model_path = utils.prepare_models(model_dir)
        max_ctx = int(os.environ.get("MAX_MODEL_LEN", 4096))

        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1, 
            n_ctx=max_ctx,
            flash_attn=ENABLE_FLASH_ATTN,
            chat_format=requested_format, # Passing None triggers auto-detection
            verbose=False
        )

        # --- FIXED LOGGING SECTION ---
        # 1. Safely handle n_ctx (Method vs Property check)
        try:
            ctx_val = llm.n_ctx() if callable(llm.n_ctx) else llm.n_ctx
        except:
            ctx_val = "Unknown"

        # 2. Get the actual name of the chat handler being used
        # If requested_format was None, this shows what the engine actually selected
        actual_format = llm.chat_format if hasattr(llm, 'chat_format') else "Unknown"
        
        print(f"--- 🛠️  Model Metadata & Config ---")
        print(f"   - Model File:     {os.path.basename(model_path)}")
        print(f"   - Context Window:  {ctx_val} tokens")
        print(f"   - Chat Format:     {actual_format}")
        print(f"   - Flash Attn:      {'ENABLED' if ENABLE_FLASH_ATTN else 'DISABLED'}")
        print(f"--- ✅ Engine Ready (RAM-only Decryption Active) ---")

    except Exception as e:
        print(f"--- ❌ Engine Initialization Failed ---")
        traceback.print_exc()
        raise e

def handler(job):
    try:
        if not ENCRYPTION_KEY:
            yield {"error": "Server ENCRYPTION_KEY missing."}
            return
            
        f = Fernet(ENCRYPTION_KEY.encode())
        input_payload = job.get('input', {})
        encrypted_input = input_payload.get('encrypted_input')
        
        if not encrypted_input:
             yield {"error": "Missing encrypted_input payload."}
             return

        decrypted_json = f.decrypt(encrypted_input.encode()).decode()
        request_data = json.loads(decrypted_json)
    except Exception as e:
        yield {"error": f"Decryption/Parsing failed: {str(e)}"}
        return

    messages = request_data.get("messages", [])
    if not messages and "prompt" in request_data:
        messages = [{"role": "user", "content": request_data["prompt"]}]

    params = request_data.get("sampling_params", {})

    try:
        # Generate stream
        stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=params.get("max_tokens", 512),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.95),
            stream=True
        )

        for chunk in stream:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    yield delta['content']

    except Exception as e:
        print(f"Inference failed: {e}")
        yield {"error": f"Inference failed: {str(e)}"}

# Trigger eager load
try:
    init_engine()
except:
    import sys
    sys.exit(1)

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})
