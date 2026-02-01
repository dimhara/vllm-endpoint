# Use a modern CUDA devel image for compilation
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install System Deps
RUN apt-get update && apt-get install -y \
    python3 python3-pip git build-essential libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Build llama-cpp-python with 2025 optimizations
# GGML_CUDA=on for NVIDIA GPUs
# GGML_FLASH_ATTN=on for faster inference (Ampere+ GPUs)
RUN CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_F16=on -DGGML_FLASH_ATTN=on" \
    pip3 install --no-cache-dir llama-cpp-python[server]

# 3. Install Secure Worker deps
RUN pip3 install --no-cache-dir runpod cryptography huggingface_hub hf_transfer

# 4. Environment Variables
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV MODEL_DIR=/models

# 5. Setup Project
WORKDIR /
COPY . .
RUN chmod +x start.sh

# Entrypoint logic is handled by start.sh to allow switching modes
ENTRYPOINT ["/bin/bash", "/start.sh"]