import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.dimension = 384  # default value for all-MiniLM-L6-v2
        
    def load_model(self) -> None:
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load SBERT model: {str(e)}")
            raise
    
    def load_faiss_index(self, index_path: str) -> None:
        try:
            self.index = faiss.read_index(index_path)
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {str(e)}")
            raise
    
    # Convert text to embedding
    def encode_text(self, text: str) -> np.ndarray:
        if not self.model:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        try:
            embedding = self.model.encode([text])
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode text: {str(e)}")
            raise
    
    # def preprocess_negative_query(self, query: str) -> str:
    #     
    #     negative_patterns = {
    #         "no technical background": "business background marketing sales expertise",
    #         "not technical": "business focused non-technical marketing",
    #         "no coding": "business development marketing sales",
    #         "non-technical": "business strategy marketing sales operations",
    #         "no programming": "business development marketing strategy",
    #         "not a developer": "business marketing sales operations",
    #         "no tech": "business operations marketing",
    #         "not technical person": "business professional marketing sales"
    #     }
        
    #     query_lower = query.lower()
    #     for negative, positive in negative_patterns.items():
    #         if negative in query_lower:
    #             processed = query_lower.replace(negative, positive)
    #             logger.info(f"Preprocessed negative query: '{query}' → '{processed}'")
    #             return processed
        
    #     return query
    
    # Normalize query embedding for cosine similarity
    def normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        normalized = embeddings.copy()
        faiss.normalize_L2(normalized)
        return normalized
    
    
    # Search for similar embeddings in FAISS index
    def search_similar(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        if not self.index:
            raise ValueError("FAISS index not loaded. Call load_faiss_index() first.")
        
        try:
            normalized_query = self.normalize_embeddings(query_embedding)
            distances, indices = self.index.search(normalized_query, k)
            
            logger.info(f"FAISS search completed - found {len(indices[0])} results")
            return distances, indices
            
        except Exception as e:
            logger.error(f"FAISS search failed: {str(e)}")
            raise
    
    # Calculate cosine similarity between two embeddings
    def calculate_cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        try:
            norm1 = embedding1 / np.linalg.norm(embedding1)
            norm2 = embedding2 / np.linalg.norm(embedding2)
            
            similarity = np.dot(norm1, norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {str(e)}")
            return 0.0