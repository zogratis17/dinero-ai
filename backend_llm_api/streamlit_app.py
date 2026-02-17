import streamlit as st
import requests
import os

# Configuration
# In production, this would be the ngrok/Cloudflare URL
# Example: "https://your-tunnel-url.trycloudflare.com/generate"
# For local testing without tunnel, usage: "http://localhost:8000/generate"
API_URL = os.getenv("LLM_API_URL", "http://localhost:8000/generate") 
API_KEY = os.getenv("LLM_API_KEY", "prod_secret_key_123")

st.set_page_config(page_title="Production LLM Client", page_icon="🤖")

st.title("🤖 Enterprise LLM Interface")
st.markdown(f"**Backend Status:** Connected to `{API_URL}`")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    custom_url = st.text_input("API URL", value=API_URL)
    api_key_input = st.text_input("API Key", value=API_KEY, type="password")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Enter your prompt for the finance model..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the decoupled API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key_input
            }
            payload = {"prompt": prompt}
            
            response = requests.post(custom_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Ollama returns the text in 'response' field
                bot_response = data.get("response", "No response field in JSON.")
                message_placeholder.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                message_placeholder.error(error_msg)
        except Exception as e:
            message_placeholder.error(f"Connection Failed: {e}")
