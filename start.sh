#!/bin/bash

# Enable fast download
export HF_HUB_ENABLE_HF_TRANSFER=1
MODEL_DIR="/models"
mkdir -p $MODEL_DIR

echo "--- Preparing Model ---"
python3 /utils.py "$MODEL_DIR"

if [ "$RUN_MODE" = "OPENAI_SERVER" ]; then
    echo "--- LaunchING Standard OpenAI API Server (Unencrypted) ---"
    # Note: Use this only in Full Pod mode. This does NOT support your custom encryption.
    python3 -m llama_cpp.server --model "$MODEL_DIR"/*.gguf --host 0.0.0.0 --port 8000 --n_gpu_layers -1 --chat_format auto
else
    echo "--- Launching Secure RunPod Worker ---"
    python3 -u /rp_handler.py
fi
