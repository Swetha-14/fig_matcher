import logging
from typing import List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from backend.models.user_model import UserProfile
from backend.models.search_request import SearchRequest
from backend.utils.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)

class CoreMatchingService:
    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.is_ready = False
        self.system_status = {
            "embedding_model": False,
            "faiss_index": False,
            "last_error": None
        }
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self, index_path: str) -> bool:
        try:
            
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.embedding_manager.load_model
            )
            self.system_status["embedding_model"] = True
            
            try:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.embedding_manager.load_faiss_index, index_path
                )
                self.system_status["faiss_index"] = True
                
            except Exception as e:
                logger.warning(f"Faiss index failed, will use brute-force: {str(e)}")
                self.system_status["faiss_index"] = False
            
            # Test embedding generation
            test_embedding = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.embedding_manager.encode_text, "test query"
            )
            
            if test_embedding is None or len(test_embedding) == 0:
                raise Exception("Embedding generation test failed")
            
            self.is_ready = True
            logger.info("Core Matching Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f" Failed to initialize: {str(e)}")
            self.system_status["last_error"] = str(e)
            return False

    async def search(self, search_request: SearchRequest, users: List[UserProfile]) -> List[Tuple[UserProfile, float]]:
        try:
            if not self.system_status["embedding_model"]:
                logger.error("Embedding model not ready")
                return []
            
            processed_query = ' '.join(search_request.query.strip().split())
            
            # Generate embedding for the search query
            query_embedding = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.embedding_manager.encode_text, processed_query
            )
            
            if self.system_status["faiss_index"]:
                scored_users = await self._faiss_search(query_embedding, users)
            else:
                scored_users = await self._brute_force_search(query_embedding, users)
            
            
            scored_users.sort(key=lambda x: x[1], reverse=True)
            
            return scored_users
            
        except Exception as e:
            logger.error(f" Search failed: {str(e)}")
            return []


    async def _faiss_search(self, query_embedding: np.ndarray, users: List[UserProfile]) -> List[Tuple[UserProfile, float]]:
        try:
            distances, indices = await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self.embedding_manager.search_similar, 
                query_embedding, 
                len(users)
            )
            
            scored_users = []
            for distance, idx in zip(distances[0], indices[0]):
                if 0 <= idx < len(users):
                    user = users[idx]
                    similarity_score = float(distance) 
                    scored_users.append((user, similarity_score))
            
            logger.debug(f"Faiss search found {len(scored_users)} results")
            return scored_users
            
        except Exception as e:
            logger.error(f" Faiss search failed: {str(e)}")
            return []

    async def _brute_force_search(self, query_embedding: np.ndarray, users: List[UserProfile]) -> List[Tuple[UserProfile, float]]:
        try:
            scored_users = []
            
            for user in users:
                user_text = user.get_combined_text_for_embedding()
                
                # Generate user embedding
                user_embedding = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self.embedding_manager.encode_text, user_text
                )
                
                if user_embedding is None or len(user_embedding) == 0:
                    continue

                # Calculate cosine similarity
                similarity_score = self.embedding_manager.calculate_cosine_similarity(
                    query_embedding[0], user_embedding
                )
                
                scored_users.append((user, similarity_score))
            
            return scored_users
            
        except Exception as e:
            logger.error(f"Brute-force search failed: {str(e)}")
            return []
