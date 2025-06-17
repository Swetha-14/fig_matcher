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


    def _preprocess_query(self, query: str) -> str:
        cleaned_query = ' '.join(query.strip().split())
        
        expansions = {
            'fintech': 'financial technology payments banking finance',
            'blockchain': 'cryptocurrency crypto smart contracts DeFi',
            'ai': 'artificial intelligence machine learning ML',
            'climate': 'renewable energy sustainability green tech',
            'healthcare': 'medical health biotech clinical',
            'marketing': 'growth B2B advertising campaigns',
            'robotics': 'automation engineering hardware',
            'venture': 'capital VC investing funding investment',
            
            'founder': 'entrepreneur startup cofounder',
            'developer': 'engineer programmer coding',
            'researcher': 'scientist PhD academic',
            'manager': 'executive director leadership',
            'designer': 'UI UX product design',
            'analyst': 'data business financial',

            'senior': 'expert experienced professional',
            'junior': 'entry level beginner graduate',
            'expert': 'senior experienced specialist',
            
            'react': 'javascript frontend web development',
            'python': 'programming data science ML',
            'solidity': 'smart contracts blockchain ethereum',
            
            'hiring': 'recruit team building positions',
            'freelance': 'contract consultant available',
            'cofounder': 'partner founding startup',
            'funding': 'investment capital seed series',
            'mentor': 'guidance advice coaching',
            'collaborate': 'partnership work together'
        }
        
        enhanced_query = cleaned_query.lower()
        
        for keyword, expansion in expansions.items():
            if keyword in enhanced_query:
                enhanced_query += f" {expansion}"
        
        return enhanced_query
    
    async def search(self, search_request: SearchRequest, users: List[UserProfile]) -> List[Tuple[UserProfile, float]]:
        try:
            if not self.system_status["embedding_model"]:
                logger.error("Embedding model not ready")
                return []
            
            processed_query = self._preprocess_query(search_request.query)
            
            # Generate embedding for the search query
            query_embedding = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.embedding_manager.encode_text, processed_query
            )
            
            if self.system_status["faiss_index"]:
                scored_users = await self._faiss_search(query_embedding, users)
            else:
                scored_users = await self._brute_force_search(query_embedding, users)
            
            filtered_users = [
            (user, score) for user, score in scored_users 
            if score >= search_request.min_similarity_threshold
        ]
            filtered_users.sort(key=lambda x: x[1], reverse=True)
            
            return filtered_users
            
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
