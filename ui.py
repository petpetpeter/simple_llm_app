import streamlit as st
import requests
import json

FASTAPI_URL = "http://fastapi:8000"

def start_new_chat():
    try:
        response = requests.post(f"{FASTAPI_URL}/start-chat")
        response.raise_for_status()
        data = response.json()
        st.session_state.session_id = data["session_id"]
        st.session_state.chat_history = []
        st.session_state.response_container.empty()
        st.session_state.user_input = ""  # Clear input on new chat
    except requests.exceptions.RequestException as e:
        st.error(f"Error starting new chat: {e}")
        st.session_state.session_id = None
        st.session_state.chat_history = []

def send_message():
    if st.session_state.session_id and st.session_state.user_input:
        message = st.session_state.user_input
        try:
            payload = {"message": message, "session_id": st.session_state.session_id}
            response = requests.post(f"{FASTAPI_URL}/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            st.session_state.chat_history.append({"role": "user", "content": message})
            st.session_state.chat_history.append({"role": "assistant", "content": data["response"]})
            st.session_state.user_input = ""  # Clear input after sending
        except requests.exceptions.RequestException as e:
            st.error(f"Error sending message: {e}")
    else:
        st.warning("Please start a new chat and enter a message.")

st.title("Ollama Chatbot")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

st.sidebar.subheader("Session Information")
st.sidebar.markdown(f"**Session ID:** `{st.session_state.session_id}`")

st.button("Start New Chat", on_click=start_new_chat)

st.session_state.response_container = st.container()

if st.session_state.chat_history:
    with st.session_state.response_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(
                    f'<div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">'
                    f'<div style="background-color: #f0f2f6; color: #333; padding: 10px; border-radius: 5px; max-width: 70%; text-align: right;">'
                    f'{message["content"]}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            elif message["role"] == "assistant":
                st.markdown(
                    f'<div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">'
                    f'<div style="background-color: #e1e1e1; color: #333; padding: 10px; border-radius: 5px; max-width: 70%; text-align: left;">'
                    f'{message["content"]}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

user_input = st.text_input("Your message:", key="user_input", on_change=send_message)

st.button("Send", on_click=send_message)