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

def get_smart_format(model_path):
    """
    Map common models to specialized handlers if 'jinja' fails.
    """
    m_lower = model_path.lower()
    if "qwen" in m_lower or "deepseek" in m_lower:
        return "qwen"
    if "llama-3" in m_lower:
        return "llama-3"
    if "gemma" in m_lower:
        return "gemma"
    return None # Let the library choose its default architecture match

def init_engine():
    global llm
    if llm is not None: return

    print("--- 🚀 Initializing llama.cpp Secure Worker ---")
    model_dir = os.environ.get("MODEL_DIR", "/models")
    
    try:
        model_path = utils.prepare_models(model_dir)
        
        # 1. Start with the most generic/native option (None)
        # This lets the library pick its best match based on architecture
        requested_format = os.environ.get("CHAT_FORMAT")
        if not requested_format:
            requested_format = get_smart_format(model_path)
            
        max_ctx = int(os.environ.get("MAX_MODEL_LEN", 4096))

        llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1, 
            n_ctx=max_ctx,
            flash_attn=ENABLE_FLASH_ATTN,
            chat_format=requested_format,
            verbose=False
        )

        ctx_val = llm.n_ctx() if callable(llm.n_ctx) else llm.n_ctx
        print(f"--- 🛠️  Model Metadata & Config ---")
        print(f"   - Model File:     {os.path.basename(model_path)}")
        print(f"   - Context Window:  {ctx_val} tokens")
        print(f"   - Chat Format:     {llm.chat_format}") 
        print(f"   - Flash Attn:      {'ENABLED' if ENABLE_FLASH_ATTN else 'DISABLED'}")
        print(f"--- ✅ Engine Ready (RAM-only Decryption Active) ---")

    except Exception as e:
        print(f"--- ❌ Engine Initialization Failed ---")
        traceback.print_exc()
        raise e

def handler(job):
    try:
        f = Fernet(ENCRYPTION_KEY.encode())
        input_payload = job.get('input', {})
        encrypted_input = input_payload.get('encrypted_input')
        
        decrypted_json = f.decrypt(encrypted_input.encode()).decode()
        request_data = json.loads(decrypted_json)
    except Exception as e:
        yield {"error": f"Decryption failed: {str(e)}"}
        return

    messages = request_data.get("messages", [])
    params = request_data.get("sampling_params", {})

    try:
        # --- PROMPT VALIDATION ---
        # We manually test the chat template here.
        # If it returns an empty string or errors, the template logic is broken.
        try:
            test_prompt = llm.create_chat_completion(messages=messages, max_tokens=1)
            # Log the prompt for the FIRST request only to help debug without flooding
            print(f"--- 📝 Internal Prompt Probe Successful (Format: {llm.chat_format}) ---")
        except Exception as e:
            print(f"--- ⚠️  Template Probe Failed: {e}. Output may be empty. ---")

        # --- GENERATE ---
        stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=params.get("max_tokens", 1024),
            temperature=params.get("temperature", 0.6),
            stream=True
        )

        token_count = 0
        for chunk in stream:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0]['delta']
                
                # Capture standard content OR DeepSeek reasoning
                token = delta.get('content') or delta.get('reasoning_content')
                
                if token:
                    token_count += 1
                    yield str(token)
        
        if token_count == 0:
             print("--- ❌ CRITICAL: 0 tokens generated. Architecture mismatch detected. ---")
             yield {"error": "The model produced no output. This is likely due to an incompatible 'jinja' chat template. Please try setting CHAT_FORMAT=llama-3 or qwen manually."}
        else:
             print(f"--- ✨ Finished (Total: {token_count} tokens) ---")

    except Exception as e:
        yield {"error": f"Inference failed: {str(e)}"}

init_engine()

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})
