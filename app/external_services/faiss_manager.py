import os
import faiss
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FaissManager:
    def __init__(self, vector_dim=384, index_path="faiss.index"):
        self.vector_dim = vector_dim
        self.index_path = index_path
        self.index = None

    def load_or_create_index(self):
        if os.path.exists(self.index_path):
            logger.info(f"Loading FAISS index from {self.index_path}...")
            self.index  = faiss.read_index(self.index_path)
            count = self.index.ntotal
            logger.info(f"Loaded FAISS index with {count} vectors.")
        else:
            logger.info("No FAISS index found, creating a new one...")
            flat_index = faiss.IndexFlatL2(self.vector_dim)
            self.index = faiss.IndexIDMap(flat_index)
            logger.info("New FAISS index created at {self.index_path}.")

    def save_index(self,index):
        if self.index is not None:
            logger.info(f"Saving FAISS index to {self.index_path}...")
            faiss.write_index(index, self.index_path)
            count = index.ntotal
            logger.info(f"Saved FAISS index with {count} vectors.")

    def add_embeddings(self, embeddings: np.ndarray, ids: np.ndarray):
        assert self.index is not None, "Index not initialized"
        self.index.add_with_ids(embeddings, ids)
        logger.debug(f"Added {len(ids)} vectors to FAISS.")

    def search(self, query_vector: np.ndarray, k: int = 5):
        assert self.index is not None, "Index not initialized"
        return self.index.search(query_vector, k)

    def reset_index(self):
        logger.info("Resetting FAISS index...")
        flat_index = faiss.IndexFlatL2(self.vector_dim)
        self.index = faiss.IndexIDMap(flat_index)
        logger.info("FAISS index reset.")

    def get_index(self):
        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        else:
            # Use IndexFlatL2 for L2 distance + wrap with IndexIDMap to support .add_with_ids
            base_index = faiss.IndexFlatL2(self.vector_dim)
            return faiss.IndexIDMap(base_index)
