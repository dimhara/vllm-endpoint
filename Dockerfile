# ==========================================
# RUNTIME
# ==========================================
FROM vllm/vllm-openai:v0.6.3

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install Runtime Deps
RUN apt-get update && apt-get install -y \
    wget curl git libgomp1 openssh-server \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python Dependencies
RUN pip3 install --no-cache-dir runpod cryptography huggingface_hub hf_transfer

# 3. Setup Directories
RUN mkdir -p /models && mkdir -p /workspace

# 4. Environment Variables
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV MODEL_DIR=/models

# 5. Copy Scripts
WORKDIR /
COPY utils.py /utils.py
COPY test_local.py /test_local.py
COPY rp_handler.py /rp_handler.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# This clears the vllm base image's entrypoint so that 
# we can override CMD normally.
ENTRYPOINT []

# DEFAULT CMD
CMD ["python3", "-u", "/rp_handler.py"]
