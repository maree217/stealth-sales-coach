"""
Stealth Sales Coach - Local AI-powered sales coaching system.

A privacy-first, completely local sales coaching system that provides
real-time insights during sales calls without recording or storing audio.
"""

__version__ = "0.1.0"
__author__ = "Sales Coach Team"

from .src.models.conversation import ConversationTurn, ConversationAnalysis, CoachingAdvice
from .src.models.config import AudioConfig, ModelConfig, CoachingConfig

__all__ = [
    "ConversationTurn",
    "ConversationAnalysis", 
    "CoachingAdvice",
    "AudioConfig",
    "ModelConfig",
    "CoachingConfig",
]