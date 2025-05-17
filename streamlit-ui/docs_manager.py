import streamlit as st
import requests

FASTAPI_URL = "http://fastapi:8000"

def docs_manager_section():
    st.markdown("---")
    st.header("📄 Document Manager")

    doc_tab = st.radio("Select Action", ["View Documents","Add Document(s)"], horizontal=True) 

    if doc_tab == "Add Document(s)":
        add_texts = st.text_area("Enter one or more documents (separate with ||)", height=200)
        if st.button("Upload Documents"):
            docs = [t.strip("||") for t in add_texts.split("\n\n") if t.strip()]
            if not docs:
                st.warning("Please enter at least one non-empty document.")
            else:
                try:
                    response = requests.post(f"{FASTAPI_URL}/docs/add-docs", json={"texts": docs})
                    response.raise_for_status()
                    st.success(response.json().get("message", "Documents uploaded!"))
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    elif doc_tab == "View Documents":
        try:
            limit = st.slider("Number of documents to fetch", 1, 100, 10)
            response = requests.get(f"{FASTAPI_URL}/docs/list-docs", params={"limit": limit})
            response.raise_for_status()
            docs = response.json().get("documents", [])
            if docs:
                for doc in docs:
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        st.write(doc["text"])
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc['id']}"):
                            try:
                                del_response = requests.delete(f"{FASTAPI_URL}/docs/delete-doc/{doc['id']}")
                                del_response.raise_for_status()
                                st.success(f"Deleted document {doc['id']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete document: {e}")
            else:
                st.info("No documents found.")
        except Exception as e:
            st.error(f"Failed to load documents: {e}")
