from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

class ActivityStatus(Enum):
    ACTIVE = "active"           # < 7 days
    RECENT = "recent"           # 7-20 days  
    INACTIVE = "inactive"       # > 30 days

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    AWAY = "away"

class NetworkingIntent(Enum):
    ACTIVELY_LOOKING = "actively_looking"
    OPEN_TO_OPPORTUNITIES = "open_to_opportunities"
    NOT_INTERESTED = "not_interested"
    HIRING = "hiring"
    SEEKING_COFOUNDER = "seeking_cofounder"
    FREELANCE_AVAILABLE = "freelance_available"
    IN_STEALTH_MODE = "in_stealth_mode"

class CurrentRole(Enum):
    TECHNICAL_FOUNDER = "technical_founder"
    BUSINESS_FOUNDER = "business_founder"
    TECHNICAL_RESEARCHER = "technical_researcher"
    PRODUCT_MANAGER = "product_manager"
    ENGINEER = "engineer"
    TECHNICAL_JUNIOR = "technical_junior"
    MARKETING_EXECUTIVE = "marketing_executive"
    TECHNICAL_SPECIALIST = "technical_specialist"
    DESIGNER = "designer"
    MARKETER = "marketer"
    INVESTOR = "investor"
    CONSULTANT = "consultant"

class ExperienceLevel(Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"
    
class PivotStatus(Enum):
    CONSISTENT = "consistent"
    EXPANDING_SCOPE = "expanding_scope"
    MAJOR_PIVOT_DETECTED = "major_pivot_detected"
    DEEPENING_EXPERTISE = "deepening_expertise" 
    NEW_USER = "new_user"

@dataclass
class Conversation:
    text: str
    timestamp: str

@dataclass
class UserProfile:
    id: int
    name: str
    bio: str
    location: str
    user_status: UserStatus
    current_role: CurrentRole
    experience_level: ExperienceLevel
    networking_intent: NetworkingIntent
    pivot_status: PivotStatus
    domain_expertise: List[str]
    skill_levels: Dict[str, str]
    remote_preference: str
    conversations: List[Conversation]
    last_active: str

    
    def days_since_last_active(self) -> Optional[int]:
        try:
            last_active_date = datetime.strptime(self.last_active, "%Y-%m-%d")
            return (datetime.now() - last_active_date).days
        except Exception:
            return None
    
    def get_activity_status(self) -> ActivityStatus:
        days = self.days_since_last_active()
        
        if days is None:
            return ActivityStatus.INACTIVE
        if days < 7:
            return ActivityStatus.ACTIVE
        elif days <= 20:
            return ActivityStatus.RECENT
        else:
            return ActivityStatus.INACTIVE
    
    def get_activity_display_text(self) -> str:
        try:
            days = self.days_since_last_active()
            
            if days is None:
                return "Activity unknown"
            
            if days == 0:
                return "Active today"
            elif days == 1:
                return "Active yesterday"
            elif days < 7:
                return f"Active {days} day{'s' if days > 1 else ''} ago"
            elif days < 30:
                weeks = days // 7
                return f"Active {weeks} week{'s' if weeks > 1 else ''} ago"
            elif days < 365:
                months = days // 30
                return f"Active {months} month{'s' if months > 1 else ''} ago"
            else:
                months = days // 30
                return f"Inactive for {months} month{'s' if months > 1 else ''}"

        except Exception as e:
            print(f"Error parsing date {self.last_active}: {e}")
            return "Activity unknown"

    
    def is_new_user(self) -> bool:
        return self.pivot_status == PivotStatus.NEW_USER
    
    def get_combined_text_for_embedding(self) -> str:
        if not self.conversations:
            return self.bio
        
        all_conversations = " ".join(conv.text for conv in self.conversations)
        return f"{self.bio} {all_conversations}"

    
    # Get conversations from the last 30 days as default unless given
    def get_recent_conversations(self, days: int = 30) -> List[Conversation]:
        if not self.conversations:
            return []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_convs = []
            
            for conv in self.conversations:
                try:
                    conv_date = datetime.strptime(conv.timestamp, "%Y-%m-%d")
                    if conv_date >= cutoff_date:
                        recent_convs.append(conv)
                except ValueError:
                    continue
            
            # If no recent conversations, return the most recent ones anyway
            if not recent_convs and self.conversations:
                sorted_convs = sorted(self.conversations, 
                                    key=lambda x: x.timestamp, reverse=True)
                recent_convs = sorted_convs[:3]
            
            return recent_convs
        
        except Exception:
            return self.conversations[:3] if self.conversations else []
    
    def has_major_pivot(self) -> bool:
        return self.pivot_status == PivotStatus.MAJOR_PIVOT_DETECTED
    
    # Create UserProfile from dictionary json data
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        conversations = []
        for conv_data in data.get('conversations', []):
            if isinstance(conv_data, dict):
                conversations.append(Conversation(
                    text=conv_data['text'],
                    timestamp=conv_data['timestamp']
                ))
        
        return cls(
            id=data['id'],
            name=data['name'],
            bio=data['bio'],
            location=data['location'],
            user_status=UserStatus(data['user_status']),
            current_role=CurrentRole(data['current_role']),
            experience_level=ExperienceLevel(data['experience_level']),
            networking_intent=NetworkingIntent(data['networking_intent']),
            pivot_status=PivotStatus(data['pivot_status']),
            domain_expertise=data['domain_expertise'],
            skill_levels=data['skill_levels'],
            remote_preference=data['remote_preference'],
            conversations=conversations,
            last_active=data['last_active']
        )
