from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import uuid

app = FastAPI()

OLLAMA_URL = "http://ollama:11434/api/chat"

# Store sessions and messages (in-memory, you could use a database for persistence)
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = None  # Optional session ID for continued chat

@app.post("/start-chat")
def start_chat():
    # Create a new session ID
    session_id = str(uuid.uuid4())
    sessions[session_id] = []  # Initialize the session with an empty message history
    return {"session_id": session_id}

@app.post("/chat")
def chat(req: ChatRequest):
    # If session_id is provided, use that session; otherwise, start a new one
    session_id = req.session_id
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid or missing session ID. Please start a new chat.")
    
    # Add the user's message to the session's message history
    sessions[session_id].append({"role": "user", "content": req.message})

    # Prepare the payload with the session's message history
    payload = {
        "model": "smollm2",  # change this to your model name if needed
        "messages": sessions[session_id],
        "stream": True
    }
    
    # Send request to Ollama and process the response
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    collected_text = ""
    
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))
            if 'message' in data and 'content' in data['message']:
                collected_text += data['message']['content']
            if data.get('done', False):
                break
    
    # Add assistant's response to the message history
    sessions[session_id].append({"role": "assistant", "content": collected_text})
    
    # Return the complete response
    return {"response": collected_text}
