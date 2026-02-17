import os
import logging
import httpx
from typing import Optional
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

class HFFinanceAgent:
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the HF Finance Agent.
        Reads HF_API_TOKEN from environment if not provided.
        Target model: zai-org/GLM-5
        """
        self.token = token or os.environ.get("HF_API_TOKEN")
        if not self.token:
            logger.error("HF_API_TOKEN is missing! Please add it to your .env file or secrets.")
            
        # Target model ID (default to GLM-5 as requested)
        self.model_id = os.environ.get("LLM_MODEL_ID", "zai-org/GLM-5")
        
        # Use Router URL (OpenAI Compatible)
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        
        # Headers for authenticated requests
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    async def call_model_async(self, prompt: str) -> str:
        """
        Call the Hugging Face Inference API asynchronously.
        Includes retries and timeout handling.
        Uses OpenAI compatible endpoint for GLM-5.
        """
        if not self.token:
            return "Error: HF_API_TOKEN is not configured."

        # GLM-5 Format: System prompt + User prompt
        # We use 'messages' format for OpenAI compatibility
        system_content = "You are a helpful finance assistant."
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]
        
        # OpenAI Compatible Payload
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.5
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                
                # Check for errors
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"HF API Error ({response.status_code}): {error_detail}")
                    
                    # Handle model loading (503) specifically which is common on free tier
                    if response.status_code == 503:
                         raise Exception("Model is currently loading. Please try again in a moment.")
                         
                    return f"Error from AI provider: {response.status_code} - {error_detail}"

                result = response.json()
                
                # Parse OpenAI compatible response
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
                elif "error" in result:
                    return f"Error: {result['error']}"
                else:
                    return str(result)
                    
            except httpx.RequestError as e:
                logger.error(f"Network error calling HF API: {e}")
                raise  # Let tenacity retry
            except Exception as e:
                logger.error(f"Unexpected error in agent: {e}")
                raise
