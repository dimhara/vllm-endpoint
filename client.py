import os
import sys
import json
import argparse
import requests
from cryptography.fernet import Fernet

# --- CONFIGURATION ---
# Set these via Environment Variables
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "YOUR_ENDPOINT_ID")
API_KEY = os.environ.get("RUNPOD_API_KEY", "YOUR_API_KEY")
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "YOUR_AES_KEY_HERE")

URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"

def encrypt_payload(messages, sampling_params, key):
    """Encrypts the OpenAI-style payload using Fernet (AES-128)."""
    f = Fernet(key.encode())
    payload = {
        "messages": messages,
        "sampling_params": sampling_params
    }
    json_data = json.dumps(payload).encode()
    return f.encrypt(json_data).decode()

def send_request(encrypted_blob):
    """Sends the encrypted blob to RunPod and returns the streaming response."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "input": {
            "encrypted_input": encrypted_blob
        }
    }
    return requests.post(URL, json=data, headers=headers, stream=True)

def chat():
    parser = argparse.ArgumentParser(description="Secure RunPod Llama.cpp Client")
    parser.add_argument("-s", "--system", default="You are a helpful assistant.", help="System prompt")
    parser.add_argument("-t", "--temp", type=float, default=0.7, help="Temperature")
    parser.add_argument("-m", "--max_tokens", type=int, default=512, help="Max tokens to generate")
    args = parser.parse_args()

    if "YOUR_" in API_KEY or "YOUR_" in ENDPOINT_ID:
        print("❌ Error: Please set your RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID.")
        return

    # Initialize local history
    history = [{"role": "system", "content": args.system}]
    
    print(f"--- 🔒 Secure Chat Session Started (Endpoint: {ENDPOINT_ID}) ---")
    print("--- (Type 'exit' or 'quit' to stop) ---")

    while True:
        try:
            user_input = input("\n👤 User: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            history.append({"role": "user", "content": user_input})

            # 1. Prepare Sampling Params
            sampling_params = {
                "max_tokens": args.max_tokens,
                "temperature": args.temp,
                "top_p": 0.95
            }

            # 2. Encrypt Entire History locally
            # Even if intercepted, RunPod/ISP sees only this random blob
            encrypted_blob = encrypt_payload(history, sampling_params, ENCRYPTION_KEY)

            # 3. Stream from RunPod
            print("🤖 AI: ", end="", flush=True)
            response = send_request(encrypted_blob)
            
            assistant_response = ""
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    # RunPod returns JSON chunks in SSE format
                    chunk = json.loads(line.decode('utf-8'))
                    
                    if chunk.get("status") == "COMPLETED":
                        # Final aggregated output if not streaming or loop ended
                        pass
                    elif "output" in chunk:
                        # Extract token from the RunPod output stream
                        token = chunk["output"]
                        
                        # Handle potential error dicts sent as tokens
                        if isinstance(token, dict) and "error" in token:
                            print(f"\n❌ Server Error: {token['error']}")
                            break
                        
                        print(token, end="", flush=True)
                        assistant_response += token
                except json.JSONDecodeError:
                    continue

            # 4. Update history for the next turn
            history.append({"role": "assistant", "content": assistant_response})
            print("") # New line after generation

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Connection Error: {e}")

    print("\n--- Session Ended ---")

if __name__ == "__main__":
    chat()
