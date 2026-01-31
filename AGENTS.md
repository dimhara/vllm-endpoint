# Agent Documentation (AGENTS.md)

## Overview
This repository contains a **secure, low-latency llama.cpp worker** optimized for RunPod Serverless. 

## Key Components
*   **`rp_handler.py`**: Serverless entry point using `llama-cpp-python` with CUDA offloading.
*   **`utils.py`**: Optimized GGUF downloader using `hf_transfer`. 
*   **`client.py`**: Reference client with Fernet encryption support.

## Configuration (Environment Variables)

| Variable | Description | Required? |
| :--- | :--- | :--- |
| `MODELS` | Format `repo_id:filename` (e.g. `Qwen/Qwen2.5-7B-GGUF:qwen2.5-7b-q4.gguf`) | **Yes** |
| `ENCRYPTION_KEY` | 32-byte URL-safe base64 Fernet key. | **Yes** |
| `MAX_MODEL_LEN` | Context window size. Default `2048`. | No |

## Goal for Agents
Ensure the `MODELS` env var points to a valid GGUF file and the `ENCRYPTION_KEY` matches between client and server. Success is defined by a coherent streaming response from `test_local.py`.

## Verification URLS
*   **llama-cpp-python**: [https://github.com/abetlen/llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
*   **RunPod Serverless**: [https://docs.runpod.io/serverless/overview](https://docs.runpod.io/serverless/overview)
