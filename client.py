import argparse
import requests
import json
import sys
from cryptography.fernet import Fernet

ENDPOINT_ID = "YOUR_ID"
API_KEY = "YOUR_API_KEY"
URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
ENCRYPTION_KEY = "YOUR_KEY"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prompt", required=True)
    args = parser.parse_args()

    f = Fernet(ENCRYPTION_KEY.encode())
    
    # Modern OpenAI Message Payload
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful, private assistant."},
            {"role": "user", "content": args.prompt}
        ],
        "sampling_params": {"max_tokens": 512, "temperature": 0.2}
    }
    
    encrypted_blob = f.encrypt(json.dumps(payload).encode()).decode()

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(
        URL, 
        json={"input": {"encrypted_input": encrypted_blob}}, 
        headers=headers, 
        stream=True
    )

    print("Response: ", end="")
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                if 'output' in data:
                    sys.stdout.write(data['output'])
                    sys.stdout.flush()
            except: pass
    print("\n")

if __name__ == "__main__":
    main()
