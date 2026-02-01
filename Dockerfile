# ==========================================
# Stage 1: Builder (Heavy, includes Compiler)
# ==========================================
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install Build Dependencies
# ninja-build and python3-dev are crucial for compiling llama-cpp-python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    ninja-build \
    cmake \
    git \
    build-essential \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup Virtual Environment
# We build into a venv so we can easily copy dependencies to the runtime stage
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Upgrade pip and build tools
RUN pip3 install --upgrade pip setuptools wheel scikit-build-core

# 4. Build llama-cpp-python with CUDA optimizations
# We compile with Flash Attention and CUDA F16 support
RUN CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_F16=on -DGGML_FLASH_ATTN=on" \
    pip3 install --no-cache-dir llama-cpp-python[server]

# 5. Install other Python dependencies (RunPod, Crypto)
RUN pip3 install --no-cache-dir runpod cryptography huggingface_hub hf_transfer

# ==========================================
# Stage 2: Runtime (Lightweight, no Compiler)
# ==========================================
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
# Set path to use the copied venv
ENV PATH="/opt/venv/bin:$PATH"
# Enable HF Transfer for fast downloads
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV MODEL_DIR=/models

# 1. Install Runtime Dependencies
# We only need python3 and basic libs, no gcc/cmake/ninja
RUN apt-get update && apt-get install -y \
    python3 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# 3. Setup Application
WORKDIR /app
COPY . .
RUN chmod +x start.sh

# 4. Entrypoint
ENTRYPOINT ["/bin/bash", "/app/start.sh"]