import streamlit as st
import requests

FASTAPI_URL = "http://fastapi:8000"

def chat_section():
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    def start_new_chat():
        try:
            response = requests.post(f"{FASTAPI_URL}/llm/start-chat")
            response.raise_for_status()
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.chat_history = []
            st.session_state.response_container.empty()
            st.session_state.user_input = ""
        except Exception as e:
            st.error(f"Error starting chat: {e}")
            st.session_state.session_id = None
            st.session_state.chat_history = []

    def send_message():
        if st.session_state.session_id and st.session_state.user_input:
            message = st.session_state.user_input
            try:
                payload = {"message": message, "session_id": st.session_state.session_id}
                response = requests.post(f"{FASTAPI_URL}/llm/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                st.session_state.chat_history.append({"role": "user", "content": message})
                st.session_state.chat_history.append({"role": "assistant", "content": data["response"]})
                st.session_state.user_input = ""
            except Exception as e:
                st.error(f"Error sending message: {e}")

    st.title("Ollama Chatbot")

    st.sidebar.subheader("Session Information")
    st.sidebar.markdown(f"**Session ID:** `{st.session_state.session_id}`")
    st.button("Start New Chat", on_click=start_new_chat)

    st.session_state.response_container = st.container()

    if st.session_state.chat_history:
        with st.session_state.response_container:
            for msg in st.session_state.chat_history:
                align = "flex-end" if msg["role"] == "user" else "flex-start"
                bg_color = "#1f1919" if msg["role"] == "user" else "#1f1919"
                st.markdown(
                    f'<div style="display: flex; justify-content: {align}; margin-bottom: 10px;">'
                    f'<div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; max-width: 70%;">'
                    f'{msg["content"]}</div></div>', unsafe_allow_html=True
                )

    st.text_input("Your message:", key="user_input", on_change=send_message)
    st.button("Send", on_click=send_message)

def rag_chat_section():
    if "rag_session_id" not in st.session_state:
        st.session_state.rag_session_id = None
    if "rag_chat_history" not in st.session_state:
        st.session_state.rag_chat_history = []
    if "rag_user_input" not in st.session_state:
        st.session_state.rag_user_input = ""

    def start_new_rag_chat():
        try:
            response = requests.post(f"{FASTAPI_URL}/llm/start-chat")
            response.raise_for_status()
            data = response.json()
            st.session_state.rag_session_id = data["session_id"]
            st.session_state.rag_chat_history = []
            st.session_state.rag_response_container.empty()
            st.session_state.rag_user_input = ""
        except Exception as e:
            st.error(f"Error starting RAG chat: {e}")
            st.session_state.rag_session_id = None
            st.session_state.rag_chat_history = []

    def send_rag_message():
        if st.session_state.rag_session_id and st.session_state.rag_user_input:
            message = st.session_state.rag_user_input
            try:
                payload = {
                    "message": message,
                    "session_id": st.session_state.rag_session_id,
                    "top_k": 3
                }
                response = requests.post(f"{FASTAPI_URL}/llm/rag-chat", json=payload)
                response.raise_for_status()
                data = response.json()

                st.session_state.rag_chat_history.append({"role": "user", "content": message})
                st.session_state.rag_chat_history.append({"role": "assistant", "content": data["response"]})
                st.session_state.rag_user_input = ""
            except Exception as e:
                st.error(f"Error sending RAG message: {e}")

    st.title("📚 RAG Chatbot")

    st.sidebar.subheader("RAG Session Info")
    st.sidebar.markdown(f"**Session ID:** `{st.session_state.rag_session_id}`")
    st.button("Start New RAG Chat", on_click=start_new_rag_chat)

    st.session_state.rag_response_container = st.container()

    if st.session_state.rag_chat_history:
        with st.session_state.rag_response_container:
            for msg in st.session_state.rag_chat_history:
                align = "flex-end" if msg["role"] == "user" else "flex-start"
                bg_color = "#1f1919" if msg["role"] == "user" else "#1f1919"
                st.markdown(
                    f'<div style="display: flex; justify-content: {align}; margin-bottom: 10px;">'
                    f'<div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; max-width: 70%;">'
                    f'{msg["content"]}</div></div>', unsafe_allow_html=True
                )

    st.text_input("Ask something with document context:", key="rag_user_input", on_change=send_rag_message)
    st.button("Send (RAG)", on_click=send_rag_message)

