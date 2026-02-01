import os
import runpod
import json
import base64
from cryptography.fernet import Fernet
from llama_cpp import Llama
import utils

# CONFIG
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
llm = None

def init_engine():
    global llm
    if llm is not None: return

    print("--- 🚀 Initializing Engine (v2025) ---")
    model_dir = os.environ.get("MODEL_DIR", "/models")
    model_path = utils.prepare_models(model_dir)

    # Load Llama with latest features
    # chat_format is set to auto to use the Jinja template in GGUF metadata
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1, 
        n_ctx=int(os.environ.get("MAX_MODEL_LEN", 4096)),
        flash_attn=True,
        verbose=False
    )
    print("--- ✅ Engine Ready (RAM-only Processing Enabled) ---")

def handler(job):
    try:
        if not ENCRYPTION_KEY:
            yield {"error": "Server ENCRYPTION_KEY missing."}
            return
            
        f = Fernet(ENCRYPTION_KEY.encode())
        input_payload = job.get('input', {})
        encrypted_input = input_payload.get('encrypted_input')
        
        # Decrypt strictly in memory
        decrypted_json = f.decrypt(encrypted_input.encode()).decode()
        request_data = json.loads(decrypted_json)
    except Exception as e:
        yield {"error": f"Decryption/Parsing failed: {str(e)}"}
        return

    # Use OpenAI-compatible format: expects 'messages' list
    messages = request_data.get("messages", [])
    if not messages and "prompt" in request_data:
        messages = [{"role": "user", "content": request_data["prompt"]}]

    params = request_data.get("sampling_params", {})

    try:
        # Latest API: native chat completion with Jinja templates
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
        yield {"error": str(e)}

# Eager initialization
init_engine()

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler, "return_aggregate_stream": True})
