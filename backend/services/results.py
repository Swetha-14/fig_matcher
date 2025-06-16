import logging
from typing import Dict, List, Set, Tuple
from backend.models.user_model import UserProfile, ActivityStatus
from backend.models.search_request import SearchRequest

logger = logging.getLogger(__name__)

class ResultsService:
    def __init__(self):
        self.domain_keywords = {
                'ai': {'ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'deep learning'},
                'fintech': {'fintech', 'financial', 'payments', 'banking', 'finance', 'payment', 'money'},
                'blockchain': {'blockchain', 'crypto', 'cryptocurrency', 'smart contracts', 'defi', 'web3'},
                'healthcare': {'healthcare', 'medical', 'health', 'biotech', 'clinical', 'pharma'},
                'climate': {'climate', 'renewable', 'sustainability', 'green', 'environment', 'carbon'},
                'startup': {'startup', 'entrepreneur', 'founding', 'founder', 'venture'}
        }
        
        self.intent_keywords = {
            'hiring': {'hire', 'hiring', 'recruit', 'position', 'job', 'team'},
            'cofounder': {'co-founder', 'cofounder', 'founding partner', 'startup partner'},
            'funding': {'funding', 'investment', 'investor', 'capital', 'seed'},
            'collaboration': {'collaborate', 'partner', 'work together', 'team up'}
        }

    def rank_users(self, scored_users: List[Tuple[UserProfile, float]], search_request: SearchRequest) -> List[Tuple[UserProfile, float]]:
        try:
            if not scored_users:
                return []
            
            # Group users by similar scores
            score_groups = {}
            for user, score in scored_users:
                rounded_score = round(score, 2)
                if rounded_score not in score_groups:
                    score_groups[rounded_score] = []
                score_groups[rounded_score].append((user, score))
            
            # Apply tie-breaking and sort
            ranked_results = []
            for score in sorted(score_groups.keys(), reverse=True):
                users_with_score = score_groups[score]
                
                if len(users_with_score) == 1:
                    ranked_results.extend(users_with_score)
                else:
                    tie_broken = self._simple_tie_breaking(users_with_score)
                    ranked_results.extend(tie_broken)
            
            return ranked_results
            
        except Exception as e:
            logger.error(f" Ranking failed: {str(e)}")
            return sorted(scored_users, key=lambda x: x[1], reverse=True)


    # Tie breaking using activity status and conversation count
    def _simple_tie_breaking(self, tied_users: List[Tuple[UserProfile, float]]) -> List[Tuple[UserProfile, float]]:
        
        def tie_score(user_tuple):
            user, similarity_score = user_tuple
            score = 0
            
            # priority 1 
            if user.get_activity_status() == ActivityStatus.ACTIVE:
                score += 0.3
            elif user.get_activity_status() == ActivityStatus.RECENT:
                score += 0.2
            else:
                score += 0.1
            
            #priortiy 2
            score += min(len(user.conversations), 5) * 0.1
            
            return similarity_score + (score * 0.05)
        
        return sorted(tied_users, key=tie_score, reverse=True)

    def create_simple_results(self, ranked_users: List[Tuple[UserProfile, float]], 
                             search_request: SearchRequest) -> List[dict]:
        try:
            results = []
            
            top_explanation = None
            if ranked_users:
                top_user, top_score = ranked_users[0]
                top_explanation = self._generate_smart_explanation(
                    top_user, top_score, search_request.query
                )
            
            for rank, (user, score) in enumerate(ranked_users, 1):
                result = {
                    "user_id": user.id,
                    "name": user.name,
                    "bio": user.bio,
                    "location": user.location,
                    "similarity_score": score,
                    "similarity_percentage": round(score * 100, 1),
                    "rank": rank,
                    "domain_expertise": user.domain_expertise,
                    "current_role": user.current_role.value,
                    "experience_level": user.experience_level.value,
                    "networking_intent": user.networking_intent.value,
                    "activity_status": user.get_activity_status().value,
                    "conversation_count": len(user.conversations),
                    "conversations": [{"text": conv.text, "timestamp": conv.timestamp} for conv in user.conversations],
                    "explanation": top_explanation if rank == 1 else None
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Results creation failed: {str(e)}")
            return []

    def _generate_smart_explanation(self, user: UserProfile, similarity_score: float, query: str) -> str:
        try:
            query_lower = query.lower()
            query_words = set(query_lower.split())
            similarity_pct = round(similarity_score * 100, 1)
            
            match_reasons = []
            
            # domain expertise
            domain_matches = self._find_domain_matches(query_words, user.domain_expertise)
            if domain_matches:
                match_reasons.append(f"deep expertise in {', '.join(domain_matches)}")
            
            # skill matching
            skill_matches = self._find_skill_matches(query_lower, user.skill_levels)
            if skill_matches:
                match_reasons.append(f"the specific skills you're looking for: {', '.join(skill_matches)}")
            
            # intent matching
            intent_match = self._find_intent_match(query_lower, user)
            if intent_match:
                match_reasons.append(intent_match)
            
            return self._build_explanation(user.name, similarity_pct, match_reasons, user)
            
        except Exception as e:
            logger.error(f"Smart explanation failed for {user.name}: {str(e)}")
            return f"{user.name} is a {round(similarity_score * 100, 1)}% match based on profile analysis."

    def _find_domain_matches(self, query_words: Set[str], user_domains: List[str]) -> List[str]:
        matches = []
        user_domains_lower = [d.lower() for d in user_domains]
        
        for domain_name, keywords in self.domain_keywords.items():
            if query_words & keywords:  
                # Check if user has matching domain
                if any(domain_name in user_domain or user_domain in domain_name 
                       for user_domain in user_domains_lower):
                    matches.append(domain_name)
        
        return matches[:3]  

    def _find_skill_matches(self, query_lower: str, skill_levels: Dict[str, str]) -> List[str]:
        matches = []
        
        for skill, level in skill_levels.items():
            if skill.lower() in query_lower:
                if level == 'expert':
                    matches.append(f"{skill} (expert)")
                elif level == 'intermediate':
                    matches.append(f"{skill} (intermediate)")
                else:
                    matches.append(skill)
        
        return matches[:3]  

    def _find_intent_match(self, query_lower: str, user: UserProfile) -> str:
        
        if any(word in query_lower for word in self.intent_keywords['hiring']):
            if user.networking_intent.value in ['actively_looking', 'open_to_opportunities']:
                return "actively seeking new opportunities, perfectly aligning with what you're seeking"
        
        if any(word in query_lower for word in self.intent_keywords['cofounder']):
            if user.networking_intent.value == 'seeking_cofounder':
                return "actively seeking co-founding opportunities, perfectly aligning with what you're seeking"
        
        if any(word in query_lower for word in self.intent_keywords['funding']):
            if user.current_role.value == 'investor':
                return "actively investing in startups, perfectly aligning with what you're seeking"
        
        return None

    def _build_explanation(self, name: str, similarity_pct: float, match_reasons: List[str], user: UserProfile) -> str:
        
        if similarity_pct >= 60:
            intro = f"{name} is an excellent {similarity_pct}% match"
        elif similarity_pct >= 40:
            intro = f"{name} shows a strong {similarity_pct}% match"
        elif similarity_pct >= 25:
            intro = f"{name} achieved a {similarity_pct}% match"
        else:
            intro = f"{name} represents a {similarity_pct}% semantic match"
        
        if match_reasons:
            primary_reason = match_reasons[0]
            if len(match_reasons) > 1:
                explanation = f"{intro} through {primary_reason}, directly matching your search requirements."
            else:
                explanation = f"{intro} with {primary_reason}."
        else:
            explanation = f"{intro} based on comprehensive profile analysis."
        
        if user.get_activity_status() == ActivityStatus.ACTIVE:
            explanation += " They're currently active on the platform."
        else:
            explanation += " They have relevant experience that aligns with your search."
        
        return explanation