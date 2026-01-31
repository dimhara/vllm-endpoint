# Agent Documentation (AGENTS.md)

## Overview
This repository contains a **secure, streaming vLLM worker** designed for the [RunPod Serverless](https://runpod.io) platform. It enforces end-to-end encryption on prompts and supports token-level streaming.

## Key Components
*   **`rp_handler.py`**: Serverless entry point (AsyncLLMEngine + Fernet decryption).
*   **`utils.py`**: Model downloader. **Optimized with `hf_transfer` (Rust)** for 10Gbps+ download speeds on RunPod.
*   **`client.py`**: Reference client (Encryption + Streaming).

## Configuration & Environment Variables

| Variable | Description | Required? | Source |
| :--- | :--- | :--- | :--- |
| `MODELS` | Comma-separated list of Hugging Face Model IDs. | **Yes** | [Hub](https://huggingface.co/models) |
| `ENCRYPTION_KEY` | 32-byte URL-safe base64 Fernet key. | **Yes** | [Docs](https://cryptography.io/en/latest/fernet/) |
| `HF_HUB_ENABLE_HF_TRANSFER` | Must be set to `1` to enable fast Rust downloads. | **Yes** | [HF Transfer](https://github.com/huggingface/hf_transfer) |
| `HF_TOKEN` | HF User Access Token (Read). | No | [Tokens](https://huggingface.co/docs/hub/security-tokens) |

## Reference Documentation

### RunPod Serverless
*   **Overview**: [https://docs.runpod.io/serverless/overview](https://docs.runpod.io/serverless/overview)
*   **Network Volumes**: [https://docs.runpod.io/serverless/storage/network-volumes](https://docs.runpod.io/serverless/storage/network-volumes)

### Hugging Face Hub
*   **Fast Downloads (hf_transfer)**: [https://huggingface.co/docs/huggingface_hub/guides/download#faster-downloads](https://huggingface.co/docs/huggingface_hub/guides/download#faster-downloads)
    *   *Agent Note*: This requires `pip install hf_transfer` and `HF_HUB_ENABLE_HF_TRANSFER=1`. This is already handled in the Dockerfile.

## Agent Actions

### Deploying to RunPod
1.  **Build**: Use the provided Dockerfile. It includes the `hf_transfer` library.
2.  **Env Vars**: Ensure `HF_HUB_ENABLE_HF_TRANSFER=1` is present (it is set in Dockerfile, but good to verify in RunPod template).
3.  **Storage**: For models >10GB, attach a Network Volume to avoid downloading on every cold start.

### Debugging
*   **Slow Downloads**: If downloads are <100MB/s on RunPod, `hf_transfer` is likely disabled. Check that the env var is set to `1` and the library is installed.
