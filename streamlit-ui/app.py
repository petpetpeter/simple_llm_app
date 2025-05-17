import streamlit as st
from chat import chat_section,rag_chat_section
from docs_manager import docs_manager_section

def main():
    chat_section()
    rag_chat_section()
    docs_manager_section()

if __name__ == "__main__":
    main()
