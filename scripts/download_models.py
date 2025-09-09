#!/usr/bin/env python3
"""Script to download required models for the sales coach."""

import os
import sys
from pathlib import Path
import urllib.request
from typing import Optional
import logging

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sales_coach.src.models.config import SalesCoachConfig


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def download_file(url: str, destination: Path, description: str = "") -> bool:
    """Download a file with progress indication."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                print(f"\r{description}: {percent}%", end='', flush=True)
        
        logger.info(f"Downloading {description}...")
        urllib.request.urlretrieve(url, destination, progress_hook)
        print()  # New line after progress
        logger.info(f"Successfully downloaded: {destination}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download {description}: {e}")
        return False


def download_whisper_model(model_size: str = "base", models_dir: Path = Path("models_cache")) -> bool:
    """Download Whisper model for whisper.cpp."""
    model_filename = f"ggml-{model_size}.bin"
    model_path = models_dir / model_filename
    
    if model_path.exists():
        logger.info(f"Whisper {model_size} model already exists at {model_path}")
        return True
    
    # Whisper.cpp model URLs
    base_url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
    model_url = f"{base_url}/{model_filename}"
    
    return download_file(
        model_url, 
        model_path, 
        f"Whisper {model_size} model"
    )


def download_llama_model(model_name: str = "llama-3.2-3b-instruct", 
                        models_dir: Path = Path("models_cache")) -> bool:
    """Download Llama model (quantized version)."""
    
    # Map model names to HuggingFace URLs
    model_urls = {
        "llama-3.2-3b-instruct": {
            "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        },
        "phi-3.5-mini": {
            "url": "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf", 
            "filename": "Phi-3.5-mini-instruct-Q4_K_M.gguf"
        }
    }
    
    if model_name not in model_urls:
        logger.error(f"Unknown model: {model_name}")
        logger.info(f"Available models: {list(model_urls.keys())}")
        return False
    
    model_info = model_urls[model_name]
    model_path = models_dir / model_info["filename"]
    
    if model_path.exists():
        logger.info(f"{model_name} model already exists at {model_path}")
        return True
    
    return download_file(
        model_info["url"],
        model_path,
        f"{model_name} model"
    )


def setup_silero_vad() -> bool:
    """Setup Silero VAD model (downloaded automatically by torch.hub)."""
    try:
        import torch
        logger.info("Setting up Silero VAD model...")
        
        # This will download the model if not already cached
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        
        logger.info("Silero VAD model ready")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup Silero VAD: {e}")
        return False


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download models for Sales Coach")
    parser.add_argument("--whisper-model", default="base", 
                       choices=["tiny", "base", "small", "medium"],
                       help="Whisper model size to download")
    parser.add_argument("--llm-model", default="phi-3.5-mini",
                       choices=["llama-3.2-3b-instruct", "phi-3.5-mini"],
                       help="LLM model to download")
    parser.add_argument("--models-dir", type=Path, default=Path("models_cache"),
                       help="Directory to store models")
    parser.add_argument("--skip-whisper", action="store_true",
                       help="Skip downloading Whisper model")
    parser.add_argument("--skip-llm", action="store_true", 
                       help="Skip downloading LLM model")
    parser.add_argument("--skip-vad", action="store_true",
                       help="Skip setting up VAD model")
    
    args = parser.parse_args()
    
    # Create models directory
    args.models_dir.mkdir(parents=True, exist_ok=True)
    
    success = True
    
    # Download Whisper model
    if not args.skip_whisper:
        success &= download_whisper_model(args.whisper_model, args.models_dir)
    
    # Download LLM model
    if not args.skip_llm:
        success &= download_llama_model(args.llm_model, args.models_dir)
    
    # Setup VAD model
    if not args.skip_vad:
        success &= setup_silero_vad()
    
    if success:
        logger.info("✅ All models downloaded successfully!")
        logger.info(f"Models stored in: {args.models_dir.absolute()}")
        logger.info("You can now run 'sales-coach start' to begin")
    else:
        logger.error("❌ Some models failed to download")
        sys.exit(1)


if __name__ == "__main__":
    main()