FROM vllm/vllm-openai:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install deps
RUN apt-get update && apt-get install -y wget curl git openssh-server && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir runpod cryptography huggingface_hub hf_transfer

# 2. Set Environment for Fast Downloads
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV VLLM_ALLOW_LONG_MAX_MODEL_LEN=1

# 3. Clear the base image entrypoint
ENTRYPOINT []

WORKDIR /
COPY . .
RUN chmod +x start.sh

CMD ["python3", "-u", "/rp_handler.py"]