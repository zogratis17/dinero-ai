# AI Chatbot Backend

This module provides an async FastAPI backend for the Dinero AI Chatbot using Hugging Face Inference API.

## Setup

1. **Environment Variables**: Ensure `.env` (in project root) has:
   ```env
   HF_API_TOKEN=hf_... (your token)
   LLM_MODEL_ID=zai-org/GLM-5
   ```

2. **Run Backend**:
   From project root:
   ```bash
   python -m backend.main
   ```
   Server runs on `http://localhost:8000`.

3. **API Endpoint**:
   - `POST /api/chat/hf-finance`
   - Body: `{ "message": "What is ROI?" }`
   - Response: `{ "reply": "ROI stands for..." }`

## Testing
Run unit and integration tests:
```bash
python -m pytest tests/test_hf_finance_agent.py tests/test_routes_chat.py
```

## Local Mode (Optional)
The architecture supports switching to a local `transformers` model loader by implementing a `LocalTransformerAgent` class and toggling via `LOCAL_MODE=true` in `.env`. Currently, only the API mode is fully implemented for lightweight execution.
