import logging
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from config import Config


logger = logging.getLogger(__name__)

class OpenSearchManager:
    def __init__(
        self,
        host: str = "opensearch",
        port: int = 9200,
        username: str = 'admin',
        password: str = 'B@ckace2025',
        use_ssl: bool = True,
        verify_certs: bool = False,
        vector_dim: int = 384,
        index_name: str = "doc-embeddings"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.vector_dim = vector_dim
        self.index_name = index_name

        self.client = None
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def connect(self):
        logger.info(f"Connecting to OpenSearch at {self.host}:{self.port}...")
        self.client = OpenSearch(
            hosts=[{"host": self.host, "port": self.port}],
            http_auth=(self.username, self.password),
            use_ssl=self.use_ssl,
            verify_certs=self.verify_certs,
            ssl_show_warn=False
        )
        info = self.client.info()
        logger.info(f"Connected to OpenSearch cluster: {info['cluster_name']}")
        return info

    def create_index(self):
        if self.client.indices.exists(self.index_name):
            logger.info(f"Deleting existing index '{self.index_name}'...")
            self.client.indices.delete(index=self.index_name)
        
        logger.info(f"Creating index '{self.index_name}' with KNN vector search...")
        self.client.indices.create(
            index=self.index_name,
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
                            "dimension": self.vector_dim
                        }
                    }
                }
            }
        )

    def index_documents(self, texts: List[str]):
        logger.info(f"Indexing {len(texts)} documents into '{self.index_name}'...")
        for i, text in enumerate(texts):
            embedding = self.model.encode(text).tolist()
            self.client.index(index=self.index_name, id=i, body={
                "content": text,
                "embedding": embedding
            })
        self.client.indices.refresh(index=self.index_name)
        logger.info("Indexing completed and index refreshed.")

    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        logger.info(f"Searching for top-{k} documents similar to: '{query}'")
        query_vec = self.model.encode(query).tolist()
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
        result = self.client.search(index=self.index_name, body=body)
        return [(hit["_source"]["content"], hit["_score"]) for hit in result["hits"]["hits"]]

    def delete_index(self):
        if self.client.indices.exists(self.index_name):
            self.client.indices.delete(index=self.index_name)
            logger.info(f"Index '{self.index_name}' deleted.")

    def disconnect(self):
        logger.info("Disconnecting from OpenSearch.")
        self.client.close()

