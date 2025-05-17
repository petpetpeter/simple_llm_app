from sentence_transformers import SentenceTransformer
import numpy as np

from opensearchpy import OpenSearch

# Replace these with your values
host = "opensearch"  # or the IP of your Docker host
port = 9200
username = "admin"
password = "R0vul@2025"  # from OPENSEARCH_INITIAL_ADMIN_PASSWORD
ca_cert_path = "/path/to/root-ca.pem"  # or use verify_certs=False for dev

# Connect over HTTPS
client = OpenSearch(
    hosts = [{"host": host, "port": port}],
    http_auth = (username, password),
    use_ssl = True,
    verify_certs = False,  # set True if you have a valid cert
    ssl_show_warn = False,
)
print(f"connected: {client.info()}")
client.cluster.put_settings(body={
    "persistent": {
        "cluster.blocks.read_only_allow_delete": None
    }
})
INDEX_NAME = "doc-embeddings"

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Define OpenSearch index with a dense vector field
def create_index():
    if client.indices.exists(INDEX_NAME):
        client.indices.delete(INDEX_NAME)
    client.indices.create(
        index=INDEX_NAME,
        body={
            "settings": {
                "index": {
                    "knn": True
                }
            },
            "mappings": {
                "properties": {
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 384  # depends on model used
                    }
                }
            }
        }
    )

# Index a batch of documents
def index_documents(texts):
    for i, text in enumerate(texts):
        vec = model.encode(text).tolist()
        client.index(index=INDEX_NAME, id=i, body={
            "content": text,
            "embedding": vec
        })
    client.indices.refresh(index=INDEX_NAME)

# Perform vector similarity search
def search(query, k=3):
    query_vec = model.encode(query).tolist()
    body = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vec,
                    "k": k
                }
            }
        }
    }
    result = client.search(index=INDEX_NAME, body=body)
    return [(hit["_source"]["content"], hit["_score"]) for hit in result["hits"]["hits"]]

# --- Usage Example ---
create_index()
index_documents([
    "The quick brown fox jumps over the lazy dog.",
    "OpenSearch is a powerful search engine.",
    "Machine learning enables intelligent applications.",
    "The fox is a clever animal.",
])

results = search("i want to have sex")
print("Top matches:")
for content, score in results:
    print(f"- {content} (score={score:.4f})")
