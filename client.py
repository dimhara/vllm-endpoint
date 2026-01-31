import argparse
import requests
import json
import sys
from cryptography.fernet import Fernet

# CONFIG - Set these!
ENDPOINT_ID = "YOUR_ID"
API_KEY = "YOUR_KEY"
URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
ENCRYPTION_KEY = "YOUR_KEY"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prompt", required=True)
    args = parser.parse_args()

    f = Fernet(ENCRYPTION_KEY.encode())
    payload = {"prompt": args.prompt, "sampling_params": {"max_tokens": 500}}
    encrypted_blob = f.encrypt(json.dumps(payload).encode()).decode()

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(
        URL, 
        json={"input": {"encrypted_input": encrypted_blob}}, 
        headers=headers, 
        stream=True
    )

    print("-" * 20)
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                if 'output' in data:
                    sys.stdout.write(data['output'])
                    sys.stdout.flush()
            except:
                pass
    print("\n" + "-" * 20)

if __name__ == "__main__":
    main()
