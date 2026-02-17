from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend.chat_agents.hf_finance_agent import HFFinanceAgent
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize agent globally for reuse (token loaded from env)
agent = HFFinanceAgent()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    
@router.post("/api/chat/hf-finance", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Async endpoint for contacting the HF Finance Agent (GLM-5).
    Enforces a strict timeout (via agent) and handles rate limiting basics.
    """
    logger.info(f"Received chat request: {request.message[:50]}...")
    
    try:
        reply = await agent.call_model_async(request.message)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail="AI service temporarily unavailable. Please try again later."
        )
