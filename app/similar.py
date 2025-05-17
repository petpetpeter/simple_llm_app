import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Sample documents
documents = [
    "The cat sits on the mat.",
    "Dogs are great pets.",
    "Artificial intelligence is the future.",
    "I love pizza and pasta.",
    "This is a document about machine learning.",
]

# Query
query = "something good"

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast & small
embedding_dim = 384  # for this model

# Compute and normalize document embeddings
doc_embeddings = model.encode(documents).astype("float32")
doc_embeddings /= np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

# Build FAISS index for cosine similarity (Inner Product = Cosine if normalized)
index = faiss.IndexFlatIP(embedding_dim)
index.add(doc_embeddings)

# Compute and normalize query embedding
query_embedding = model.encode([query]).astype("float32")
query_embedding /= np.linalg.norm(query_embedding, axis=1, keepdims=True)

# Search
top_k = 3
D, I = index.search(query_embedding, top_k)

# Show results
print(f"Query: {query}\n")
print("Top results:")
for rank, idx in enumerate(I[0]):
    print(f"{rank + 1}. {documents[idx]} (score: {D[0][rank]:.4f})")
