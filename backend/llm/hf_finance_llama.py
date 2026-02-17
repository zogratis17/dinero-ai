
import os
import requests
import logging

# Configure logging
logger = logging.getLogger(__name__)

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
# Using zai-org/GLM-5 as a reliable substitute for the discontinued finance-Llama3-8B model
MODEL_ID = "zai-org/GLM-5" 
API_URL = "https://router.huggingface.co/v1/chat/completions"

def generate_response(prompt: str) -> str:
    """
    Generate a response using HF Router API (OpenAI compatible).
    Currently uses GLM-5 as a stable backend.
    """
    if not HF_API_TOKEN:
        logger.error("HF_API_TOKEN environment variable is missing.")
        return "Error: HF_API_TOKEN is missing. Please set it in your environment."
    
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # OpenAI Chat Completion Format
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"HF API Error: {response.status_code} - {response.text}")
            return "Model is temporarily unavailable. Please try again."
            
        result = response.json()
        
        # Parse OpenAI format
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
            
        return str(result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "Model is temporarily unavailable. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Model is temporarily unavailable. Please try again."
