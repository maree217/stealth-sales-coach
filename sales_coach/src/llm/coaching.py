"""Sales coaching system using LLM for analysis and advice generation."""

import json
import logging
import time
import threading
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    Llama = None

from ..models.config import ModelConfig, CoachingConfig
from ..models.conversation import (
    ConversationTurn, ConversationAnalysis, CoachingAdvice, 
    CoachingResponse, ConversationState, ConversationStage,
    CoachingCategory, CoachingPriority, Speaker
)


logger = logging.getLogger(__name__)


class SalesCoachLLM:
    """LLM-based sales coaching system."""
    
    def __init__(self, model_config: ModelConfig, coaching_config: CoachingConfig):
        self.model_config = model_config
        self.coaching_config = coaching_config
        
        self.model: Optional[Llama] = None
        self.is_loaded = False
        
        # Coaching state
        self.conversation_state = ConversationState(
            session_id=f"session_{int(time.time())}",
            started_at=datetime.now()
        )
        
        # Callbacks
        self.coaching_callback: Optional[Callable[[CoachingResponse], None]] = None
        
        # Threading for non-blocking analysis
        self.analysis_queue: List[Dict[str, Any]] = []
        self.analysis_thread: Optional[threading.Thread] = None
        self.is_analyzing = False
        
        logger.info("Initializing sales coaching LLM")
    
    def load_model(self) -> bool:
        """Load the LLM model."""
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python not available. Install with: pip install llama-cpp-python")
            return False
        
        model_path = self._get_model_path()
        if not model_path or not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False
        
        try:
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.model_config.llm_context_length,
                n_threads=4,  # Optimize for M3 MacBook Air
                n_gpu_layers=-1,  # Use Metal acceleration on macOS
                use_mmap=True,
                use_mlock=False,
                verbose=False
            )
            
            self.is_loaded = True
            logger.info(f"Loaded LLM model: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            return False
    
    def _get_model_path(self) -> Optional[Path]:
        """Get path to the LLM model file."""
        if self.model_config.llm_model_path:
            return Path(self.model_config.llm_model_path)
        
        # Common locations for Llama models
        model_patterns = [
            f"*{self.model_config.llm_model_name}*.gguf",
            f"*llama*3.2*3b*.gguf",
            f"*phi*3.5*mini*.gguf"
        ]
        
        search_dirs = [
            Path("models_cache"),
            Path.home() / ".cache" / "huggingface" / "hub",
            Path("/usr/local/share/llm-models"),
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for pattern in model_patterns:
                    matches = list(search_dir.glob(pattern))
                    if matches:
                        return matches[0]  # Return first match
        
        return None
    
    def set_coaching_callback(self, callback: Callable[[CoachingResponse], None]) -> None:
        """Set callback for coaching responses."""
        self.coaching_callback = callback
    
    def add_conversation_turn(self, turn: ConversationTurn) -> None:
        """Add a new conversation turn."""
        self.conversation_state.add_turn(turn)
        
        # Trigger analysis if conditions are met
        if self._should_analyze_conversation():
            self._queue_analysis()
    
    def _should_analyze_conversation(self) -> bool:
        """Determine if conversation should be analyzed now."""
        turns = self.conversation_state.turns
        
        if len(turns) < self.coaching_config.min_transcript_length:
            return False
        
        # Check if enough time has passed since last coaching
        if self.conversation_state.recent_coaching:
            last_coaching = self.conversation_state.recent_coaching[-1]
            time_since_last = (datetime.now() - last_coaching.generated_at).total_seconds()
            
            if time_since_last < self.coaching_config.coaching_interval:
                return False
        
        return True
    
    def _queue_analysis(self) -> None:
        """Queue conversation for analysis."""
        analysis_data = {
            "turns": self.conversation_state.get_recent_turns(
                self.coaching_config.conversation_context_window
            ),
            "conversation_state": self.conversation_state,
            "timestamp": datetime.now()
        }
        
        self.analysis_queue.append(analysis_data)
        
        # Start analysis thread if not running
        if not self.is_analyzing:
            self.start_analysis()
    
    def start_analysis(self) -> None:
        """Start background analysis thread."""
        if self.is_analyzing:
            return
        
        self.is_analyzing = True
        self.analysis_thread = threading.Thread(target=self._analysis_worker)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        logger.info("Started coaching analysis thread")
    
    def stop_analysis(self) -> None:
        """Stop background analysis thread."""
        if not self.is_analyzing:
            return
        
        self.is_analyzing = False
        
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=2.0)
        
        logger.info("Stopped coaching analysis thread")
    
    def _analysis_worker(self) -> None:
        """Background worker for conversation analysis."""
        logger.info("Coaching analysis worker started")
        
        while self.is_analyzing:
            if not self.analysis_queue:
                time.sleep(0.1)
                continue
            
            try:
                # Get analysis request
                analysis_data = self.analysis_queue.pop(0)
                
                # Perform analysis
                coaching_response = self._analyze_conversation(
                    analysis_data["turns"],
                    analysis_data["conversation_state"]
                )
                
                if coaching_response:
                    # Add to conversation state
                    self.conversation_state.add_coaching(coaching_response)
                    
                    # Call callback if set
                    if self.coaching_callback:
                        try:
                            self.coaching_callback(coaching_response)
                        except Exception as e:
                            logger.error(f"Error in coaching callback: {e}")
                
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}")
        
        logger.info("Coaching analysis worker stopped")
    
    def _analyze_conversation(self, turns: List[ConversationTurn], 
                            conversation_state: ConversationState) -> Optional[CoachingResponse]:
        """Analyze conversation and generate coaching advice."""
        if not self.is_loaded or not turns:
            return None
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(turns, conversation_state)
            
            # Generate response
            start_time = time.time()
            response = self.model(
                prompt,
                max_tokens=self.model_config.llm_max_tokens,
                temperature=self.model_config.llm_temperature,
                stop=["<|end|>", "<|user|>", "<|system|>"],
                echo=False
            )
            
            processing_time = time.time() - start_time
            logger.debug(f"LLM processing time: {processing_time:.2f}s")
            
            # Parse response
            response_text = response['choices'][0]['text'].strip()
            coaching_response = self._parse_coaching_response(response_text, len(turns))
            
            return coaching_response
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return None
    
    def _create_analysis_prompt(self, turns: List[ConversationTurn], 
                              conversation_state: ConversationState) -> str:
        """Create analysis prompt for the LLM."""
        
        # Format conversation
        conversation_text = ""
        for turn in turns[-10:]:  # Last 10 turns
            speaker_label = turn.speaker.value
            conversation_text += f"{speaker_label}: {turn.text}\n"
        
        # Calculate talk ratio
        talk_ratio = conversation_state.get_talk_ratio()
        talk_ratio_desc = "balanced"
        if talk_ratio > 2.0:
            talk_ratio_desc = "sales rep talking too much"
        elif talk_ratio < 0.5:
            talk_ratio_desc = "customer talking much more"
        
        # Current stage context
        current_stage = conversation_state.current_stage.value
        
        prompt = f"""<|system|>
You are an expert sales coach analyzing live sales conversations. Provide structured coaching advice in JSON format.<|end|>
<|user|>
Analyze this sales conversation:

CONTEXT:
- Stage: {current_stage}
- Talk ratio: {talk_ratio:.1f} ({talk_ratio_desc})
- Duration: {conversation_state.total_duration/60:.1f} minutes

CONVERSATION:
{conversation_text}

Provide coaching advice in this exact JSON format:
{{
    "analysis": {{
        "customer_concern": "main concern or null",
        "conversation_stage": "{current_stage}",
        "customer_sentiment": "positive|neutral|negative"
    }},
    "primary_advice": {{
        "priority": "HIGH|MEDIUM|LOW",
        "category": "QUESTIONING|LISTENING|OBJECTION_HANDLING|VALUE_PROPOSITION|CLOSING|RAPPORT_BUILDING",
        "insight": "brief insight",
        "suggested_action": "specific action"
    }},
    "confidence": 0.8
}}<|end|>
<|assistant|>"""

        return prompt
    
    def _parse_coaching_response(self, response_text: str, context_window: int) -> Optional[CoachingResponse]:
        """Parse LLM response into structured coaching response."""
        try:
            # Clean up response text
            response_text = response_text.strip()
            if not response_text:
                logger.debug("Empty response from LLM")
                return None
            
            # Log the raw response for debugging
            logger.debug(f"Raw LLM response: {response_text[:200]}...")
            
            # Multiple extraction strategies
            json_text = None
            
            # Strategy 1: Look for JSON code blocks
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0]
            
            # Strategy 2: Look for { } blocks
            if not json_text and "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    json_text = response_text[start:end]
            
            # Strategy 3: Use the whole response
            if not json_text:
                json_text = response_text
            
            json_text = json_text.strip()
            if not json_text:
                logger.debug("Empty response after JSON extraction")
                return None
            
            logger.debug(f"Extracted JSON: {json_text[:200]}...")
            
            # Parse JSON
            response_data = json.loads(json_text)
            
            # Create analysis object
            analysis = ConversationAnalysis(
                customer_concern=response_data["analysis"].get("customer_concern"),
                sales_rep_approach=response_data["analysis"].get("sales_rep_approach"),
                conversation_stage=ConversationStage(response_data["analysis"]["conversation_stage"]),
                key_topics=response_data["analysis"].get("key_topics", []),
                customer_sentiment=response_data["analysis"].get("customer_sentiment"),
                engagement_level=response_data["analysis"].get("engagement_level")
            )
            
            # Create primary advice
            advice_data = response_data["primary_advice"]
            primary_advice = CoachingAdvice(
                priority=CoachingPriority(advice_data["priority"]),
                category=CoachingCategory(advice_data["category"]),
                insight=advice_data["insight"],
                suggested_action=advice_data["suggested_action"],
                example_phrase=advice_data.get("example_phrase"),
                timing=advice_data.get("timing")
            )
            
            # Create coaching response
            coaching_response = CoachingResponse(
                analysis=analysis,
                primary_advice=primary_advice,
                confidence=response_data["confidence"],
                context_window=context_window
            )
            
            return coaching_response
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse coaching response: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
    
    def force_analysis(self) -> Optional[CoachingResponse]:
        """Force immediate analysis of current conversation."""
        if not self.conversation_state.turns:
            return None
        
        recent_turns = self.conversation_state.get_recent_turns(
            self.coaching_config.conversation_context_window
        )
        
        return self._analyze_conversation(recent_turns, self.conversation_state)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation."""
        return {
            "session_id": self.conversation_state.session_id,
            "started_at": self.conversation_state.started_at.isoformat(),
            "total_turns": len(self.conversation_state.turns),
            "total_duration": self.conversation_state.total_duration,
            "talk_ratio": self.conversation_state.get_talk_ratio(),
            "current_stage": self.conversation_state.current_stage.value,
            "recent_coaching_count": len(self.conversation_state.recent_coaching),
            "participant_count": self.conversation_state.participant_count
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coaching system statistics."""
        return {
            "is_loaded": self.is_loaded,
            "is_analyzing": self.is_analyzing,
            "analysis_queue_size": len(self.analysis_queue),
            "model_config": {
                "model_name": self.model_config.llm_model_name,
                "context_length": self.model_config.llm_context_length,
                "max_tokens": self.model_config.llm_max_tokens,
                "temperature": self.model_config.llm_temperature
            },
            "conversation_summary": self.get_conversation_summary()
        }


def create_coaching_system(model_config: ModelConfig, 
                         coaching_config: CoachingConfig) -> Optional[SalesCoachLLM]:
    """Factory function to create coaching system."""
    coach = SalesCoachLLM(model_config, coaching_config)
    
    if not coach.load_model():
        logger.error("Failed to load LLM model for coaching")
        return None
    
    return coach