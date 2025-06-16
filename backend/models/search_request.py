from typing import List, Optional
from dataclasses import dataclass

#SEE
@dataclass
class SearchFilters:
    """Optional filters for search"""
    required_skills: Optional[List[str]] = None
    excluded_skills: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    remote_only: Optional[bool] = None
    networking_intents: Optional[List[str]] = None  
    exclude_new_users: Optional[bool] = None
    exclude_inactive: Optional[bool] = None

@dataclass
class SearchRequest:
    
    query: str
    k: int = 5 
    min_similarity_threshold: float = 0.2
    filters: Optional[SearchFilters] = None
    current_user_id: Optional[int] = None 
