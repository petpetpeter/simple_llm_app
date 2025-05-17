from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from sentence_transformers import SentenceTransformer
from external_services import osm  # must provide `client`, `index_name`, `create_index`
from uuid import uuid4

router = APIRouter()

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_NAME = osm.index_name
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# --- Models ---
class DocumentAddRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1)

class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=100)

# --- Routes ---

@router.get("/health")
def health_check():
    try:
        return {"status": osm.client.cluster.health()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenSearch not healthy: {str(e)}")

@router.post("/add-docs")
def add_documents(req: DocumentAddRequest):
    try:
        if not osm.client.indices.exists(INDEX_NAME):
            osm.create_index()

        for text in req.texts:
            doc_id = osm.get_next_doc_id() if hasattr(osm, "get_next_doc_id") else str(uuid4())
            embedding = embedding_model.encode(text).tolist()
            osm.client.index(index=INDEX_NAME, id=doc_id, body={"content": text, "embedding": embedding})

        osm.client.indices.refresh(index=INDEX_NAME)
        return {"message": f"{len(req.texts)} documents added."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Add failed: {str(e)}")

@router.post("/search-docs")
def search_documents(req: DocumentSearchRequest):
    try:
        query_vec = embedding_model.encode(req.query).tolist()
        body = {
            "size": req.top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vec,
                        "k": req.top_k
                    }
                }
            }
        }
        response = osm.client.search(index=INDEX_NAME, body=body)
        hits = response.get("hits", {}).get("hits", [])
        results = [{"id": h["_id"], "text": h["_source"]["content"], "score": h["_score"]} for h in hits]
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/get-doc/{doc_id}")
def get_document(doc_id: str):
    try:
        if not osm.client.exists(index=INDEX_NAME, id=doc_id):
            raise HTTPException(status_code=404, detail="Document not found")
        doc = osm.client.get(index=INDEX_NAME, id=doc_id)
        return {"id": doc["_id"], "content": doc["_source"]["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")

@router.delete("/delete-doc/{doc_id}")
def delete_document(doc_id: str):
    try:
        if not osm.client.exists(index=INDEX_NAME, id=doc_id):
            raise HTTPException(status_code=404, detail="Document not found")
        osm.client.delete(index=INDEX_NAME, id=doc_id)
        return {"message": f"Document {doc_id} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.delete("/reset-index")
def reset_index():
    try:
        if osm.client.indices.exists(INDEX_NAME):
            osm.client.indices.delete(index=INDEX_NAME)
        osm.create_index()
        return {"message": "Index reset successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset index: {str(e)}")

@router.get("/list-docs")
def list_documents(limit: int = 100):
    """
    List available documents from the index.
    """

    try:
        if not osm.client.indices.exists(INDEX_NAME):
            raise HTTPException(status_code=404, detail="Index does not exist.")

        response = osm.client.search(
            index=INDEX_NAME,
            body={
                "size": limit,
                "_source": ["content"],
                "query": {
                    "match_all": {}
                }
            }
        )
        hits = response.get("hits", {}).get("hits", [])
        docs = [{"id": h["_id"], "text": h["_source"]["content"]} for h in hits]
        print(f"Docs: {docs}")
        return {"documents": docs}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

