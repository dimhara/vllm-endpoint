# llama.cpp Secure Worker

A high-performance, security-focused serverless worker for [llama.cpp](https://github.com/ggerganov/llama.cpp) (via `llama-cpp-python`) on RunPod.

This worker is designed for **low-latency cold starts** and **privacy**. It is ideal for "the odd query" where vLLM's heavy initialization and VRAM pre-allocation would be too slow or resource-intensive.

## 🚀 Why llama.cpp for Serverless?

| Feature | vLLM | llama.cpp (This Worker) |
| :--- | :--- | :--- |
| **Cold Start** | 40-60s (Slow due to CUDA graphs) | **2-5s (Nearly Instant)** |
| **VRAM Usage** | Massive (Pre-allocates cache) | **Lean (Fits to model size)** |
| **Format** | Safetensors / Raw | **GGUF (Quantized & Optimized)** |
| **Stability** | High throughput (Batching) | **High Reliability (Low overhead)** |

---

## 🔒 Security Features

*   **End-to-End Prompt Encryption**: Prompts are encrypted using **Fernet (AES-128)** on the client. The server decrypts them strictly in memory.
*   **Encrypted Transport**: All communication happens over HTTPS, with the added layer of symmetric encryption for the sensitive prompt payload.
*   **In-Memory Processing**: Prompt contexts are handled in RAM/VRAM and are not persisted to disk.

---

## 1. Setup & Configuration

### Environment Variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `MODELS` | **Required.** Format: `repo_id:filename` | `Qwen/Qwen2.5-7B-Instruct-GGUF:qwen2.5-7b-instruct-q4_k_m.gguf` |
| `ENCRYPTION_KEY` | **Required.** 32-byte URL-safe base64 key. | `Generate one using the command below.` |
| `MAX_MODEL_LEN` | Context window size (tokens). | `4096` (Default: 2048) |
| `HF_HUB_ENABLE_HF_TRANSFER` | Enables fast Rust downloads. | `1` (Highly Recommended) |

### Generate an Encryption Key
You and the worker must share the same key. Generate it via:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 2. Deployment

### Building the Image
The Dockerfile compiles `llama-cpp-python` with **CUDA support**.

```bash
docker build -t your-username/llama-cpp-secure-worker:latest .
docker push your-username/llama-cpp-secure-worker:latest
```

### RunPod Settings
*   **Container Image**: `your-username/llama-cpp-secure-worker:latest`
*   **Docker Command**: Leave blank for Serverless, or `/start.sh` for Interactive Pod.
*   **Container Disk**: Ensure at least 20GB for model storage.

---

## 3. Usage

### Local Testing (Within a Pod)
To verify the engine, encryption, and streaming are working without making an external API call:
```bash
# Set your model and key
export MODELS="Qwen/Qwen2.5-0.5B-Instruct-GGUF:qwen2.5-0.5b-instruct-q4_k_m.gguf"
export ENCRYPTION_KEY="your-key-here"

# Run the test
python3 test_local.py --prompt "Explain the benefits of GGUF models."
```

### Remote Client
Update `client.py` with your `ENDPOINT_ID`, `API_KEY`, and `ENCRYPTION_KEY`.
```bash
python client.py -p "What is the capital of France?"
```

---

## 4. Performance Tips

1.  **Use RunPod Cached Models**: In the RunPod Endpoint settings, set the **Model** field to the Hugging Face repo ID (e.g., `Qwen/Qwen2.5-7B-Instruct-GGUF`). This will mount the model cache to `/runpod-volume/`, allowing the worker to skip the download step almost entirely.
2.  **Quantization**: Use `Q4_K_M` or `Q5_K_M` GGUF files for the best balance of speed and intelligence.
3.  **VRAM Offloading**: This worker is configured to offload **all layers** (`n_gpu_layers=-1`) to the GPU by default for maximum speed.

---

## 🛠️ Project Structure
*   `rp_handler.py`: Entry point for RunPod. Handles the async streaming loop.
*   `utils.py`: Fast model downloader using `hf_transfer`.
*   `client.py`: Client-side encryption and stream consumer.
*   `test_local.py`: Local verification script.
*   `Dockerfile`: Optimized for NVIDIA CUDA 12.1.
