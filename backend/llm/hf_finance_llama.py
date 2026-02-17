
import os
import requests
import logging

# Configure logging
logger = logging.getLogger(__name__)

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
MODEL_ID = "instruction-pretrain/finance-Llama3-8B"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

def generate_response(prompt: str) -> str:
    """
    Generate a response from the Finance Llama3 8B model via Hugging Face Inference API.
    
    Args:
        prompt (str): The user's input prompt.
        
    Returns:
        str: The generated text response or an error message.
    """
    if not HF_API_TOKEN:
        logger.error("HF_API_TOKEN environment variable is missing.")
        return "Error: HF_API_TOKEN is missing. Please set it in your environment."
    
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"HF API Error: {response.status_code} - {response.text}")
            return "Model is temporarily unavailable. Please try again."
            
        result = response.json()
        
        # Safely extract text from response list or dict
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            return result[0].get("generated_text", str(result))
        elif isinstance(result, dict) and "generated_text" in result:
            return result.get("generated_text", str(result))
            
        return str(result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        return "Model is temporarily unavailable. Please try again."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "Model is temporarily unavailable. Please try again."
