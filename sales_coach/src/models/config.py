"""Configuration models for the sales coach system."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from pathlib import Path
import os


class AudioConfig(BaseModel):
    """Audio processing configuration."""
    
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    chunk_duration: float = Field(default=5.0, description="Audio chunk duration in seconds")
    input_device: Optional[str] = Field(default=None, description="Audio input device name")
    
    # VAD settings
    vad_threshold: float = Field(default=0.02, description="Voice activity detection threshold")
    vad_model: str = Field(default="silero", description="VAD model to use")
    
    # Buffer settings
    max_buffer_size: int = Field(default=100, description="Maximum audio buffer size")
    buffer_cleanup_interval: float = Field(default=60.0, description="Buffer cleanup interval in seconds")
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        if v not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError('Sample rate must be one of: 8000, 16000, 22050, 44100, 48000')
        return v
    
    @validator('chunk_duration')
    def validate_chunk_duration(cls, v):
        if v <= 0 or v > 30:
            raise ValueError('Chunk duration must be between 0 and 30 seconds')
        return v


class ModelConfig(BaseModel):
    """AI model configuration."""
    
    # Whisper settings
    whisper_model: str = Field(default="tiny", description="Whisper model size")
    whisper_device: str = Field(default="auto", description="Device for Whisper inference")
    
    # LLM settings
    llm_model_path: Optional[str] = Field(default=None, description="Path to LLM model file")
    llm_model_name: str = Field(default="llama-3.2-3b", description="LLM model name")
    llm_context_length: int = Field(default=2048, description="LLM context window size")
    llm_max_tokens: int = Field(default=200, description="Maximum tokens for LLM response")
    llm_temperature: float = Field(default=0.3, description="LLM sampling temperature")
    
    # Diarization settings
    diarization_model: str = Field(default="pyannote", description="Speaker diarization model")
    min_speakers: int = Field(default=2, description="Minimum number of speakers")
    max_speakers: int = Field(default=4, description="Maximum number of speakers")
    
    @validator('whisper_model')
    def validate_whisper_model(cls, v):
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if v not in valid_models:
            raise ValueError(f'Whisper model must be one of: {valid_models}')
        return v
    
    @validator('llm_temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v


class CoachingConfig(BaseModel):
    """Sales coaching behavior configuration."""
    
    # Timing settings
    coaching_interval: float = Field(default=30.0, description="Coaching interval in seconds")
    min_transcript_length: int = Field(default=3, description="Minimum transcript turns for coaching")
    
    # Coaching behavior
    priority_threshold: float = Field(default=0.7, description="Threshold for high priority advice")
    max_simultaneous_advice: int = Field(default=2, description="Maximum simultaneous coaching items")
    
    # Context settings
    conversation_context_window: int = Field(default=10, description="Number of recent turns to analyze")
    enable_conversation_memory: bool = Field(default=True, description="Enable full conversation tracking")
    
    # Categories and priorities
    enabled_categories: List[str] = Field(
        default=[
            "QUESTIONING",
            "LISTENING", 
            "OBJECTION_HANDLING",
            "VALUE_PROPOSITION",
            "CLOSING",
            "RAPPORT_BUILDING"
        ],
        description="Enabled coaching categories"
    )
    
    @validator('coaching_interval')
    def validate_coaching_interval(cls, v):
        if v < 5 or v > 300:
            raise ValueError('Coaching interval must be between 5 and 300 seconds')
        return v


class SystemConfig(BaseModel):
    """System-level configuration."""
    
    # Resource limits
    max_memory_percent: float = Field(default=50.0, description="Maximum memory usage percentage")
    max_cpu_percent: float = Field(default=60.0, description="Maximum CPU usage percentage")
    
    # Paths
    models_cache_dir: Path = Field(default=Path("models_cache"), description="Models cache directory")
    logs_dir: Path = Field(default=Path("logs"), description="Logs directory")
    config_dir: Path = Field(default=Path("config"), description="Configuration directory")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_to_file: bool = Field(default=True, description="Enable file logging")
    log_rotation: bool = Field(default=True, description="Enable log rotation")
    
    # Privacy
    store_transcripts: bool = Field(default=False, description="Store conversation transcripts")
    store_audio: bool = Field(default=False, description="Store audio recordings")
    anonymize_logs: bool = Field(default=True, description="Anonymize sensitive data in logs")
    
    @validator('max_memory_percent', 'max_cpu_percent')
    def validate_percentages(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class SalesCoachConfig(BaseModel):
    """Complete sales coach system configuration."""
    
    audio: AudioConfig = Field(default_factory=AudioConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    coaching: CoachingConfig = Field(default_factory=CoachingConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    
    @classmethod
    def from_file(cls, config_path: Path) -> "SalesCoachConfig":
        """Load configuration from file."""
        if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif config_path.suffix.lower() == '.json':
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        return cls(**config_data)
    
    def to_file(self, config_path: Path) -> None:
        """Save configuration to file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
            import yaml
            with open(config_path, 'w') as f:
                yaml.safe_dump(self.dict(), f, default_flow_style=False, indent=2)
        elif config_path.suffix.lower() == '.json':
            import json
            with open(config_path, 'w') as f:
                json.dump(self.dict(), f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")
    
    def create_directories(self) -> None:
        """Create necessary directories."""
        self.system.models_cache_dir.mkdir(parents=True, exist_ok=True)
        self.system.logs_dir.mkdir(parents=True, exist_ok=True)
        self.system.config_dir.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Optional[Path] = None) -> SalesCoachConfig:
    """Load configuration with environment overrides."""
    
    # Start with defaults
    config = SalesCoachConfig()
    
    # Load from file if specified
    if config_path and config_path.exists():
        config = SalesCoachConfig.from_file(config_path)
    
    # Environment variable overrides
    env_overrides = {
        'SALES_COACH_WHISPER_MODEL': ('models', 'whisper_model'),
        'SALES_COACH_LLM_MODEL_PATH': ('models', 'llm_model_path'),
        'SALES_COACH_AUDIO_DEVICE': ('audio', 'input_device'),
        'SALES_COACH_LOG_LEVEL': ('system', 'log_level'),
        'SALES_COACH_COACHING_INTERVAL': ('coaching', 'coaching_interval'),
    }
    
    for env_var, (section, key) in env_overrides.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            # Convert types as needed
            if key in ['coaching_interval']:
                value = float(value)
            elif key in ['min_transcript_length', 'max_simultaneous_advice']:
                value = int(value)
            elif key in ['store_transcripts', 'store_audio', 'anonymize_logs']:
                value = value.lower() in ['true', '1', 'yes', 'on']
                
            setattr(getattr(config, section), key, value)
    
    return config