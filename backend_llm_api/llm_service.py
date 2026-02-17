import os
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from root directory
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
# Using the official Meta Llama 3 8B Instruct model which is supported on the Router API
MODEL_ID = os.getenv("LLM_MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct")
API_KEY = os.getenv("LLM_API_KEY", "prod_secret_key_123")
# Use the OpenAI-compatible endpoint on the new router
API_URL = "https://router.huggingface.co/v1/chat/completions"

if not HF_TOKEN:
    logger.warning("HF_TOKEN is not set. LLM requests will fail.")

logger.info(f"Using model: {MODEL_ID}")

def require_api_key(f):
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return jsonify({"detail": "Invalid API Key"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", 
        "provider": "Hugging Face Router API (OpenAI Compatible)",
        "model": MODEL_ID
    })

@app.route("/generate", methods=["POST"])
@require_api_key
def generate():
    data = request.json
    if not data or "prompt" not in data:
        return jsonify({"detail": "Prompt is required"}), 400
    
    prompt = data["prompt"]
    
    try:
        logger.info(f"Generating content with model {MODEL_ID}...")
        
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Using OpenAI-compatible format supported by the Router
        payload = {
            "model": MODEL_ID,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            logger.error(f"HF API Error: {response.status_code} - {response.text}")
            return jsonify({"detail": f"LLM Provider Error: {response.status_code} {response.text}"}), 502
            
        result = response.json()
        
        # Parse OpenAI-compatible response: choices[0].message.content
        if "choices" in result and len(result["choices"]) > 0:
            response_text = result["choices"][0]["message"]["content"]
        else:
            response_text = str(result)
        
        return jsonify({"response": response_text})

    except Exception as e:
        logger.error(f"Error calling HF API: {e}")
        return jsonify({"detail": f"LLM Provider Error: {str(e)}"}), 502

if __name__ == "__main__":
    logger.info("Starting LLM Service on port 8000...")
    app.run(host="0.0.0.0", port=8000)
