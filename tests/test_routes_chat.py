from fastapi.testclient import TestClient
from backend.routes.chat import router
from backend.main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@patch("backend.routes.chat.agent.call_model_async")
def test_chat_endpoint(mock_call):
    # Mock successful agent call
    mock_call.return_value = "You should save 20%."
    
    response = client.post("/api/chat/hf-finance", json={"message": "budget?"})
    assert response.status_code == 200
    assert response.json() == {"reply": "You should save 20%."}

@patch("backend.routes.chat.agent.call_model_async")
def test_chat_failure(mock_call):
    # Mock failure
    mock_call.side_effect = Exception("Service Down")
    
    response = client.post("/api/chat/hf-finance", json={"message": "budget?"})
    assert response.status_code == 503
    assert "AI service temporarily unavailable" in response.json()["detail"]
