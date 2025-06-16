import os
import sys
import logging
import time
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


from backend.models.user_model import UserProfile
from backend.models.search_request import SearchRequest
from backend.services.core_matching import CoreMatchingService
from backend.services.results import ResultsService
from data_loader import users_data


# Logger setup 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchResponse(BaseModel):
    query: str
    results: List[dict]
    total_found: int
    search_time_ms: float
    top_match_explanation: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None
    suggestions: Optional[List[str]] = []
    
    

class AppState:
    def __init__(self):
        self.core_matching_service: Optional[CoreMatchingService] = None
        self.results_service: Optional[ResultsService] = None
        
        self.user_profiles_cache: Dict[int, UserProfile] = {}
        self.cache_timestamp: Optional[float] = None
        
        self.initialization_status = {
            "services_loaded": False,
            "cache_loaded": False,
            "last_error": None
        }

app_state = AppState()

class SearchRequestAPI(BaseModel):
    
    query: str = Field(..., min_length=1, description="User search query")
    k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    current_user_id: Optional[int] = Field(default=None, description="Current user ID (excluded from results)")
    min_similarity_threshold: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum similarity threshold")

    @field_validator('query') 
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            return ""  
        
        cleaned = ' '.join(v.strip().split())
        return cleaned

@asynccontextmanager
async def lifespan(api:FastAPI):
    logger.info("Starting Figbox Matcher API...")
    
    try:
        await initialize_services()
        await load_user_cache()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        app_state.initialization_status["last_error"] = str(e)
    
    yield
    
    logger.info("Shutting down Figbox Matcher API...")

# Initialize FastAPI application
app = FastAPI(
    title="Figbox Matcher API",
    version="1.0.0",
    description="Intelligent User Matching System",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_services() -> bool:
    try:
        logger.info("Initializing application services...")

        app_state.results_service = ResultsService()
        app_state.core_matching_service = CoreMatchingService()
        
        # Initialize semantic search engine
        index_path = "embeddings/faiss_index.bin"
        success = await app_state.core_matching_service.initialize(index_path)
        
        if success:
            app_state.initialization_status["services_loaded"] = True
            logger.info("All services initialized successfully")
            return True
        else:
            raise Exception("Core matching service initialization failed")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {str(e)}")
        app_state.initialization_status["last_error"] = str(e)
        return False

# Load user profiles into memory cache for fast access.
async def load_user_cache() -> bool:
    try:
        
        app_state.user_profiles_cache.clear()
        loaded_count = 0
        
        for i, user_data in enumerate(users_data):
            try:
                user_profile = UserProfile.from_dict(user_data)
                app_state.user_profiles_cache[user_profile.id] = user_profile
                loaded_count += 1
            except Exception as e:
                logger.warning(f"Failed to load user {i+1}: {str(e)}")
                continue
        
        if loaded_count == 0:
            raise Exception("No users could be loaded")
        
        app_state.cache_timestamp = time.time()
        app_state.initialization_status["cache_loaded"] = True
        
        logger.info(f"Loaded {loaded_count} user profiles successfully")
        return True
        
    except Exception as e:
        logger.error(f"User cache loading failed: {str(e)}")
        app_state.initialization_status["last_error"] = str(e)
        return False


def get_all_users() -> List[UserProfile]:
    return list(app_state.user_profiles_cache.values())

def exclude_current_user(users: List[UserProfile], current_user_id: Optional[int]) -> List[UserProfile]:
    if current_user_id is None:
        return users
    
    filtered_users = [user for user in users if user.id != current_user_id]
    
    if len(filtered_users) != len(users):
        logger.info(f"Excluded current user {current_user_id}: {len(users)} -> {len(filtered_users)} users")
    
    return filtered_users


@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy" if app_state.initialization_status["services_loaded"] else "unhealthy",
            "timestamp": time.time(),
            "services_ready": app_state.initialization_status["services_loaded"],
            "users_loaded": len(app_state.user_profiles_cache),
            "last_error": app_state.initialization_status.get("last_error")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }


@app.get("/users")
async def get_users():
    try:
        users = get_all_users()
        users_data = []
        
        for user in users:
            user_dict = {
                "id": user.id,
                "name": user.name,
                "bio": user.bio,
                "location": user.location,
                "domain_expertise": user.domain_expertise,
                "current_role": user.current_role.value,
                "experience_level": user.experience_level.value,
                "networking_intent": user.networking_intent.value,
                "activity_status": user.get_activity_status().value,
                "conversation_count": len(user.conversations),
                "remote_preference": user.remote_preference
            }
            users_data.append(user_dict)
        
        return {
            "users": users_data,
            "total": len(users_data),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f" Get users failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")
    
    
# Pilot
@app.post("/search", response_model=SearchResponse)
async def search_users(request: SearchRequestAPI):
    
    start_time = time.time()
    
    if not request.query or not request.query.strip():
        return SearchResponse(
            query=request.query or "",
            results=[],
            total_found=0,
            search_time_ms=(time.time() - start_time) * 1000,
            error_message="Please enter a search query",
            suggestions=[
                "Try: 'AI developer'",
                "Try: 'fintech expert'", 
                "Try: 'need a co-founder'"
            ]
        )
    
    try:
        logger.info(f" Search request: '{request.query}' (excluding user {request.current_user_id})")
        
        # Verify services are ready
        if not app_state.initialization_status["services_loaded"]:
            raise HTTPException(
                status_code=503, 
                detail="Search services are not ready. Please try again later."
            )
        
        # Get all users and exclude current user
        all_users = get_all_users()
        if not all_users:
            raise HTTPException(status_code=503, detail="No user data available")
        
        available_users = exclude_current_user(all_users, request.current_user_id)
        
        if not available_users:
            return SearchResponse(
                query=request.query,
                results=[],
                total_found=0,
                search_time_ms=(time.time() - start_time) * 1000,
                error_message="No users available for matching",
                suggestions=["Please try again later when more users are available"]
            )
            
        
        search_request = SearchRequest(
            query=request.query,
            k=request.k,
            current_user_id=request.current_user_id,
            min_similarity_threshold=request.min_similarity_threshold
        )
         
        scored_users = await app_state.core_matching_service.search(search_request, available_users)
        
        if not scored_users:
            return SearchResponse(
                query=request.query,
                results=[],
                total_found=0,
                search_time_ms=(time.time() - start_time) * 1000,
                error_message="No matches found",
                suggestions=[
                    "Try using different keywords",
                    "Make your query more specific",
                    "Consider alternative terms for your requirements"
                ]
            )
        
        ranked_users = app_state.results_service.rank_users(scored_users, search_request)
        
        results = app_state.results_service.create_simple_results(
            ranked_users[:request.k], search_request
        )

        search_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=results,  
            total_found=len(results),
            search_time_ms=search_time,
            top_match_explanation=results[0]["explanation"] if results else None,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Search failed: {str(e)}", exc_info=True)
        return SearchResponse(
            query=request.query,
            results=[],
            total_found=0,
            search_time_ms=search_time,
            error_message="Internal search error occurred",
            suggestions=["Please try again with a different query"],
            status="error"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )