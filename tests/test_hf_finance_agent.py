import pytest
import os
from unittest.mock import AsyncMock, patch
from backend.chat_agents.hf_finance_agent import HFFinanceAgent

# Minimal mock for httpx response (OpenAI Compatible)
class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json

@pytest.mark.asyncio
async def test_call_model_success():
    with patch.dict(os.environ, {"HF_API_TOKEN": "test_key", "LLM_MODEL_ID": "test/model"}):
        agent = HFFinanceAgent()
        
        # Mock httpx.AsyncClient context manager
        # OpenAI response structure
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Finance advice"
                    }
                }
            ]
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = MockResponse(mock_response_data)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            # Also mock __aenter__ / __aexit__
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            result = await agent.call_model_async("Help me")
            assert result == "Finance advice"
