# Use a lean CUDA devel image to compile llama-cpp
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install System Deps
RUN apt-get update && apt-get install -y \
    python3 python3-pip git build-essential libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Build llama-cpp-python with CUDA support
# This ensures the LLM runs on the GPU
RUN CMAKE_ARGS="-DGGML_CUDA=on" pip3 install llama-cpp-python

# 3. Install Secure Worker deps
RUN pip3 install --no-cache-dir runpod cryptography huggingface_hub hf_transfer

# 4. Environment Variables
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV MODEL_DIR=/models

# 5. Setup Project
WORKDIR /
COPY . .
RUN chmod +x start.sh

# Reset Entrypoint for RunPod compatibility
ENTRYPOINT []
CMD ["python3", "-u", "/rp_handler.py"]
