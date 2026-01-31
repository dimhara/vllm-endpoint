import os
import runpod
import json
import asyncio
from cryptography.fernet import Fernet
from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
from vllm.utils import random_uuid
import utils

# CONFIG
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
MAX_CONCURRENCY = int(os.environ.get("MAX_CONCURRENCY", 100))

# GLOBAL ENGINE
llm_engine = None

async def init_engine():
    global llm_engine
    if llm_engine is not None: return

    print("--- 🚀 Initializing vLLM Engine ---")
    
    model_dir = os.environ.get("MODEL_DIR", "/models")
    model_path = utils.prepare_models(model_dir)
    if not model_path: raise RuntimeError("No model path resolved.")

    # Robust context length parsing
    env_max_len = os.environ.get("MAX_MODEL_LEN")
    if not env_max_len or str(env_max_len).lower() == "auto":
        max_model_len = None # This is the "auto" behavior for the Python API
    else:
        try:
            max_model_len = int(env_max_len)
        except ValueError:
            print(f"Warning: Could not parse MAX_MODEL_LEN '{env_max_len}' as int. Defaulting to None (auto).")
            max_model_len = None

    # Enable trust_remote_code via env var
    trust_remote_code = os.environ.get("TRUST_REMOTE_CODE", "0") == "1"

    engine_args = AsyncEngineArgs(
        model=model_path,
        gpu_memory_utilization=float(os.environ.get("GPU_MEMORY_UTILIZATION", "0.95")),
        max_model_len=max_model_len, # Must be int or None
        dtype="auto",
        trust_remote_code=trust_remote_code,
        enforce_eager=False,
        max_num_seqs=256,
        disable_log_stats=False
    )

    llm_engine = AsyncLLMEngine.from_engine_args(engine_args)
    
    # Correct way to log the derived context length in V1 engine
    derived_len = llm_engine.model_config.max_model_len
    print(f"--- ✅ vLLM Engine Ready (Context Length: {derived_len}) ---")
    

async def handler(job):
    global llm_engine
    
    # 1. DECRYPT INPUT
    try:
        if not ENCRYPTION_KEY:
            yield {"error": "Server ENCRYPTION_KEY missing."}
            return
        
        input_data = job.get('input', {})
        encrypted_input = input_data.get('encrypted_input')
        
        if not encrypted_input:
            yield {"error": "No encrypted_input provided."}
            return

        f = Fernet(ENCRYPTION_KEY.encode())
        decrypted_json = f.decrypt(encrypted_input.encode()).decode()
        request_data = json.loads(decrypted_json)
        
    except Exception as e:
        yield {"error": f"Decryption failed: {str(e)}"}
        return

    # 2. PARSE PROMPT & PARAMS
    prompt = request_data.get("prompt")
    if not prompt:
        yield {"error": "No prompt in payload."}
        return

    params_dict = request_data.get("sampling_params", {})
    sampling_params = SamplingParams(
        temperature=params_dict.get("temperature", 0.7),
        max_tokens=params_dict.get("max_tokens", 512),
        top_p=params_dict.get("top_p", 1.0),
        stop=params_dict.get("stop", [])
    )

    request_id = random_uuid()
    
    # 3. GENERATE & STREAM (Continuous Batching enabled via shared engine)
    try:
        results_generator = llm_engine.generate(prompt, sampling_params, request_id)
        previous_text = ""
        
        async for request_output in results_generator:
            full_text = request_output.outputs[0].text
            delta = full_text[len(previous_text):]
            previous_text = full_text
            yield delta

    except Exception as e:
        yield {"error": str(e)}


# 1. Initialize the engine
loop = asyncio.get_event_loop()
loop.run_until_complete(init_engine())

if __name__ == "__main__":
    runpod.serverless.start({
        "handler": handler,
        "concurrency_modifier": lambda x: MAX_CONCURRENCY,
        "return_aggregate_stream": True
    })
