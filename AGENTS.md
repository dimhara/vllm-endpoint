# Agent Documentation (AGENTS.md)

## Overview
This repository contains a **secure, streaming vLLM worker** designed for the [RunPod Serverless](https://runpod.io) platform. It differs from standard workers by enforcing end-to-end encryption on prompts and supporting token-level streaming via Python asynchronous generators.

## Key Components
*   **`rp_handler.py`**: The serverless entry point. It initializes the `vllm.AsyncLLMEngine`, handles Fernet decryption of inputs, and streams text deltas back to the RunPod Orchestrator.
*   **`utils.py`**: A helper script that uses `huggingface_hub` to download full model snapshots. It supports RunPod Network Volumes (caching) to minimize cold-start times.
*   **`client.py`**: A reference implementation for the client side, handling payload encryption and stream consumption.

## Configuration & Environment Variables

| Variable | Description | Required? | Source Documentation |
| :--- | :--- | :--- | :--- |
| `MODELS` | Comma-separated list of Hugging Face Model IDs (e.g., `meta-llama/Meta-Llama-3-8B-Instruct`). | **Yes** | [Hugging Face Models](https://huggingface.co/models) |
| `ENCRYPTION_KEY` | 32-byte URL-safe base64 Fernet key. | **Yes** | [Cryptography (Fernet)](https://cryptography.io/en/latest/fernet/) |
| `HF_TOKEN` | Hugging Face User Access Token (Read). Required for gated models. | No | [HF Tokens](https://huggingface.co/docs/hub/security-tokens) |
| `HF_HOME` | Directory for HF cache. Defaults to `/runpod-volume/huggingface-cache` if volume attached. | No | [HF Environment Variables](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables) |
| `GPU_MEMORY_UTILIZATION` | Float (0.0 - 1.0). Percentage of VRAM vLLM should reserve. Default `0.95`. | No | [vLLM Engine Args](https://docs.vllm.ai/en/latest/models/engine_args.html) |

## Reference Documentation (Verified URLs)

### RunPod Serverless
*   **Overview & Architecture**: [https://docs.runpod.io/serverless/overview](https://docs.runpod.io/serverless/overview)
*   **Handler Functions (Python SDK)**: [https://docs.runpod.io/serverless/workers/handlers/handler-functions](https://docs.runpod.io/serverless/workers/handlers/handler-functions)
*   **Deployment**: [https://docs.runpod.io/serverless/endpoints/deploy-endpoint](https://docs.runpod.io/serverless/endpoints/deploy-endpoint)

### RunPod Storage & Caching
*   **Network Volumes (Persistent Storage)**: [https://docs.runpod.io/serverless/storage/network-volumes](https://docs.runpod.io/serverless/storage/network-volumes)
    *   *Agent Note*: To enable caching, attach a Network Volume to the endpoint and set `HF_HOME` to a path within that volume (e.g., `/runpod-volume/huggingface-cache`).

### Hugging Face Hub
*   **Snapshot Download**: [https://huggingface.co/docs/huggingface_hub/guides/download#download-an-entire-repository](https://huggingface.co/docs/huggingface_hub/guides/download#download-an-entire-repository)
*   **Environment Variables**: [https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables)

## Agent Actions

### Deploying to RunPod
1.  **Build Image**: Use the `Dockerfile` to build the image (ensure ~20GB disk space is available).
2.  **Push to Registry**: Push to Docker Hub or GitHub Container Registry.
3.  **Create Template**: On RunPod, create a serverless template using this image.
4.  **Set Env Vars**: Add `MODELS`, `ENCRYPTION_KEY`, and optional `HF_TOKEN`.

### Debugging
*   **Cold Start Issues**: If the worker times out on the first request, the model download is likely too slow. Recommend attaching a Network Volume to persist the model between restarts.
*   **Decryption Errors**: Ensure the `ENCRYPTION_KEY` used in `client.py` exactly matches the environment variable on the server.
