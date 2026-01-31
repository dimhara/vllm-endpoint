import os
import runpod
import json
from cryptography.fernet import Fernet
from llama_cpp import Llama
import utils

# CONFIG
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
llm = None

def init_engine():
    global llm
    if llm is not None:
        return

    print("--- 🚀 Initializing llama.cpp Engine ---")
    
    # 1. Download Model
    model_dir = os.environ.get("MODEL_DIR", "/models")
    model_path = utils.prepare_models(model_dir)

    # 2. Load Llama
    # n_gpu_layers=-1 means "put everything on the GPU"
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1, 
        n_ctx=int(os.environ.get("MAX_MODEL_LEN", 2048)),
        verbose=False
    )
    print("--- ✅ llama.cpp Engine Ready ---")

def handler(job):
    # 1. DECRYPT INPUT
    try:
        if not ENCRYPTION_KEY:
            yield {"error": "Server ENCRYPTION_KEY missing."}
            return
            
        f = Fernet(ENCRYPTION_KEY.encode())
        input_payload = job.get('input', {})
        encrypted_input = input_payload.get('encrypted_input')
        
        decrypted_json = f.decrypt(encrypted_input.encode()).decode()
        request_data = json.loads(decrypted_json)
    except Exception as e:
        yield {"error": f"Decryption/Parsing failed: {str(e)}"}
        return

    prompt = request_data.get("prompt")
    params = request_data.get("sampling_params", {})

    # 2. GENERATE & STREAM
    try:
        # Simple Chat template for Qwen/Llama
        formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        stream = llm(
            prompt=formatted_prompt,
            max_tokens=params.get("max_tokens", 512),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 0.95),
            stream=True
        )

        for chunk in stream:
            token = chunk['choices'][0]['text']
            if token:
                yield token

    except Exception as e:
        yield {"error": str(e)}

# Load model on startup
init_engine()

if __name__ == "__main__":
    runpod.serverless.start({
        "handler": handler,
        "return_aggregate_stream": True
    })

