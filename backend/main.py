from fastapi import FastAPI
import uvicorn
import logging
from backend.routes import chat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dinero AI Chat Backend", version="1.0.0")

# Include routers
app.include_router(chat.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "HF Finance Agent Backend"}

if __name__ == "__main__":
    logger.info("Starting Dinero AI Chat Backend on port 8000...")
    # Run Uvicorn server (async)
    uvicorn.run(app, host="0.0.0.0", port=8000)
