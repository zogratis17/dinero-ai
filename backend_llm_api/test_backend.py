import requests
import json
import time

def test_api():
    print("Testing API backend at http://localhost:8000/generate...")
    
    headers = {
        "x-api-key": "prod_secret_key_123"
    }
    
    prompt = {"prompt": "What is the capital of Japan?"}
    
    try:
        response = requests.post("http://localhost:8000/generate", json=prompt, headers=headers)
        
        if response.status_code == 200:
            print("\nResponse from API:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\nFailed to get response: {response.status_code}")
            print(f"Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("\nConnection refused. Make sure `python llm_service.py` is running!")

if __name__ == "__main__":
    test_api()
