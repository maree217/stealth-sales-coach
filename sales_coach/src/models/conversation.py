"""Conversation and coaching models for the sales coach system."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class Speaker(str, Enum):
    """Speaker identification."""
    SALES_REP = "SALES_REP"
    CUSTOMER = "CUSTOMER" 
    UNKNOWN = "UNKNOWN"


class ConversationStage(str, Enum):
    """Sales conversation stages."""
    DISCOVERY = "DISCOVERY"
    QUALIFICATION = "QUALIFICATION"
    SOLUTION_PRESENTATION = "SOLUTION_PRESENTATION"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    CLOSING = "CLOSING"
    FOLLOW_UP = "FOLLOW_UP"


class CoachingCategory(str, Enum):
    """Categories of coaching advice."""
    QUESTIONING = "QUESTIONING"
    LISTENING = "LISTENING"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    VALUE_PROPOSITION = "VALUE_PROPOSITION"
    CLOSING = "CLOSING"
    RAPPORT_BUILDING = "RAPPORT_BUILDING"


class CoachingPriority(str, Enum):
    """Priority levels for coaching advice."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConversationTurn(BaseModel):
    """Single turn in the conversation."""
    
    speaker: Speaker = Field(description="Who is speaking")
    text: str = Field(description="What was said")
    timestamp: datetime = Field(description="When this was said")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Transcription confidence")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")
    
    def __str__(self) -> str:
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.speaker.value}: {self.text}"


class ConversationAnalysis(BaseModel):
    """Analysis of conversation segment."""
    
    customer_concern: Optional[str] = Field(
        None, 
        description="Main concern or question from customer"
    )
    sales_rep_approach: Optional[str] = Field(
        None,
        description="Current approach being used by sales rep"
    )
    conversation_stage: ConversationStage = Field(
        description="Current stage of sales conversation"
    )
    key_topics: List[str] = Field(
        default_factory=list,
        description="Key topics discussed in this segment"
    )
    customer_sentiment: Optional[Literal["positive", "neutral", "negative"]] = Field(
        None,
        description="Customer's apparent sentiment"
    )
    engagement_level: Optional[Literal["high", "medium", "low"]] = Field(
        None,
        description="Customer's engagement level"
    )


class CoachingAdvice(BaseModel):
    """Structured coaching advice."""
    
    priority: CoachingPriority = Field(description="Priority level of this advice")
    category: CoachingCategory = Field(description="Category of coaching advice")
    insight: str = Field(description="Brief coaching insight (max 80 words)")
    suggested_action: str = Field(description="Specific action to take (max 50 words)")
    example_phrase: Optional[str] = Field(
        None,
        description="Example phrase to use"
    )
    timing: Optional[str] = Field(
        None,
        description="When to apply this advice"
    )


class CoachingResponse(BaseModel):
    """Complete coaching response."""
    
    analysis: ConversationAnalysis = Field(description="Analysis of the conversation")
    primary_advice: CoachingAdvice = Field(description="Primary coaching advice")
    secondary_advice: Optional[CoachingAdvice] = Field(
        None, 
        description="Secondary coaching advice if applicable"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, 
        description="Confidence in the coaching assessment"
    )
    context_window: int = Field(
        description="Number of conversation turns analyzed"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When this coaching was generated"
    )


class ConversationState(BaseModel):
    """Current state of the ongoing conversation."""
    
    session_id: str = Field(description="Unique session identifier")
    started_at: datetime = Field(description="When conversation started")
    turns: List[ConversationTurn] = Field(
        default_factory=list,
        description="All conversation turns"
    )
    current_stage: ConversationStage = Field(
        default=ConversationStage.DISCOVERY,
        description="Current conversation stage"
    )
    participant_count: int = Field(
        default=2,
        description="Number of identified participants"
    )
    
    # Analytics
    total_duration: float = Field(
        default=0.0,
        description="Total conversation duration in seconds"
    )
    sales_rep_talk_time: float = Field(
        default=0.0,
        description="Total sales rep talk time in seconds"
    )
    customer_talk_time: float = Field(
        default=0.0,
        description="Total customer talk time in seconds"
    )
    
    # Recent coaching
    recent_coaching: List[CoachingResponse] = Field(
        default_factory=list,
        description="Recent coaching responses"
    )
    
    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a new conversation turn."""
        self.turns.append(turn)
        
        # Update talk times
        if turn.duration:
            if turn.speaker == Speaker.SALES_REP:
                self.sales_rep_talk_time += turn.duration
            elif turn.speaker == Speaker.CUSTOMER:
                self.customer_talk_time += turn.duration
            
            self.total_duration += turn.duration
    
    def get_recent_turns(self, count: int = 10) -> List[ConversationTurn]:
        """Get the most recent conversation turns."""
        return self.turns[-count:] if len(self.turns) >= count else self.turns
    
    def get_talk_ratio(self) -> float:
        """Get sales rep to customer talk time ratio."""
        if self.customer_talk_time == 0:
            return float('inf') if self.sales_rep_talk_time > 0 else 0.0
        return self.sales_rep_talk_time / self.customer_talk_time
    
    def add_coaching(self, coaching: CoachingResponse) -> None:
        """Add coaching response and maintain recent history."""
        self.recent_coaching.append(coaching)
        
        # Keep only last 20 coaching responses
        if len(self.recent_coaching) > 20:
            self.recent_coaching = self.recent_coaching[-20:]


class SpeakerProfile(BaseModel):
    """Profile for speaker identification and characteristics."""
    
    speaker: Speaker = Field(description="Speaker identity")
    voice_characteristics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Voice characteristics for identification"
    )
    speaking_patterns: Dict[str, Any] = Field(
        default_factory=dict,
        description="Speaking patterns and style"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Confidence in speaker identification"
    )
    samples_analyzed: int = Field(
        default=0,
        description="Number of audio samples used to build this profile"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When this profile was last updated"
    )
    
    def update_profile(self, audio_features: Dict[str, Any]) -> None:
        """Update speaker profile with new audio features."""
        # This would be implemented based on the specific
        # voice analysis features being used
        self.samples_analyzed += 1
        self.last_updated = datetime.now()
        
        # Simple confidence update - more samples = higher confidence
        # Up to a maximum of 0.95
        self.confidence = min(0.95, self.samples_analyzed * 0.1)