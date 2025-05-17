from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
import uuid
import logging
logger = logging.getLogger()

from external_services import osm
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_NAME = osm.index_name
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Create a router instance
router = APIRouter()
OLLAMA_URL = "http://ollama:11434/api/chat"

# Store sessions and messages (in-memory, consider a database for persistence)
# This state is now managed within this router's scope
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = None  # Optional session ID for continued chat

@router.post("/start-chat")
def start_chat():
    """
    Starts a new chat session and returns a unique session ID.
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = []  # Initialize the session with an empty message history
    return {"session_id": session_id}

@router.post("/chat")
def chat(req: ChatRequest):
    """
    Handles sending a message to the Ollama model within a specific session.
    """
    session_id = req.session_id
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid or missing session ID. Please start a new chat using /llm/start-chat.")

    # Add the user's message to the session's message history
    sessions[session_id].append({"role": "user", "content": req.message})

    # Prepare the payload with the session's message history
    payload = {
        "model": "llama3",  # change this to your model name if needed
        "messages": sessions[session_id],
        "stream": True # Keep streaming enabled
    }

    collected_text = ""
    try:
        # Send request to Ollama and process the streaming response
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) # Added timeout
        response.raise_for_status() # Check for HTTP errors

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'message' in data and 'content' in data['message']:
                        collected_text += data['message']['content']
                    # Check if the response indicates completion (structure might vary slightly by model/Ollama version)
                    if data.get('done', False):
                         # Optional: You might want to capture final context or metrics here if available
                        break
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON line: {line}") # Log decoding errors
                except Exception as e:
                    print(f"Error processing stream line: {e}") # Log other processing errors


    except requests.exceptions.RequestException as e:
        # Log the error and return an informative HTTP exception
        print(f"Error communicating with Ollama: {e}")
        raise HTTPException(status_code=503, detail=f"Could not communicate with Ollama service: {e}")
    except Exception as e:
        # Catch unexpected errors during streaming/processing
        print(f"Unexpected error during chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


    # Add assistant's complete response to the message history only if successful
    if collected_text:
         sessions[session_id].append({"role": "assistant", "content": collected_text})
    else:
        # Handle cases where Ollama might not have responded with content
        # You might want to return an error or a specific message
        print(f"Warning: No content received from Ollama for session {session_id}")
        # Optionally raise an exception or return a specific response
        # raise HTTPException(status_code=500, detail="No response content received from Ollama.")
        return {"response": "[No content received from model]"}


    # Return the complete response
    return {"response": collected_text}

class RAGChatRequest(BaseModel):
    message: str
    session_id: str = None
    top_k: int = 3  # Number of similar docs to retrieve


@router.post("/rag-chat")
def rag_chat(req: RAGChatRequest):
    session_id = req.session_id
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=400, detail="Invalid or missing session ID. Please start a new chat using /llm/start-chat.")

    # Step 1: Embed the query
    query_vec = embedding_model.encode(req.message).tolist()

    # Step 2: Retrieve top-k relevant documents
    try:
        response = osm.search(query=req.message, k=req.top_k)
        context_chunks = [doc for doc, score in response]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG retrieval failed: {e}")

    # Step 3: Prepare prompt with structured format
    documents_formatted = "\n".join(f"- {doc}" for doc in context_chunks)
    system_prompt = (
        "You are a helpful assistant. Try to use the information from the documents below together with your knowledge to answer the question. Do not try to combine all documents — only use the ones that are clearly relevant to the question.\n\n"
        f"### Documents:\n{documents_formatted}\n\n"
        f"### Question:\n{req.message}\n\n### Answer:"
    )

    # Build conversation history
    messages = [{"role": "system", "content": system_prompt}]
    logger.warning(f"RAG chat messages: {messages}")

    # Step 4: Send to Ollama
    payload = {
        "model": "llama3",
        "messages": messages,
        "stream": True
    }

    collected_text = ""
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'message' in data and 'content' in data['message']:
                        collected_text += data['message']['content']
                    if data.get('done', False):
                        break
                except Exception:
                    continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama call failed: {e}")

    # Save and return
    sessions[session_id].append({"role": "user", "content": req.message})
    sessions[session_id].append({"role": "assistant", "content": collected_text})

    return {
        "response": collected_text.strip(),
        "documents": context_chunks
    }
