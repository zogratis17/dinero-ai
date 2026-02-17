# Decoupled LLM Inference Architecture

An industry-standard, resilient architecture for serving local LLMs using Flask (Backend) and Vanilla JS/Next.js (Frontend).

## Architecture

1.  **Inference Layer (Local)**: Ollama runs the raw model.
2.  **Service Layer (Flask)**: Validates input, handles auth, logs metrics, and proxies to Ollama.
3.  **Transport Layer (Tunnel)**: Cloudflare/Ngrok exposes the Service Layer.
4.  **Presentation Layer (Frontend)**:
    -   **Local**: Simple HTML/JS Client (`index.html`) running on port 8501.
    -   **Production**: Next.js API Route (`nextjs_api_route.ts`) deployed on Vercel.

## Quick Start (Running Now)

The system is already running in the background!

-   **Backend API**: [http://localhost:8000/generate](http://localhost:8000/generate)
-   **Frontend UI**: [http://localhost:8501](http://localhost:8501)

### 1. Verify Backend
The backend (`llm_service.py`) is running on port 8000. It proxies requests to Ollama.

### 2. Use the Frontend
Open **[http://localhost:8501](http://localhost:8501)** in your browser.
This is a lightweight, dependency-free chat interface that connects to your local backend.

### 3. Public Exposure (Optional)
To share this with the world or use with Vercel:

```bash
# Expose the API
cloudflared tunnel --url http://localhost:8000
```
Then update the `API_URL` in `index.html` or your Vercel configs.

## Project Structure

-   `llm_service.py`: **The Core**. A Flask app that wraps Ollama.
-   `index.html`: **The Client**. A pure HTML/JS app (Streamlit alternative).
-   `nextjs_api_route.ts`: **The Cloud Integration**. Copy this to your Next.js app.
-   `requirements.txt`: Python dependencies.

## Why Flask & HTML?
We switched from FastAPI/Streamlit to Flask/HTML to ensure maximum compatibility with your current Windows/MSYS2 environment. The *architectural pattern* remains identical: strictly decoupled frontend and backend.
