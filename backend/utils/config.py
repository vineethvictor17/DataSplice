"""
Configuration management for DataSplice backend.

Loads settings from environment variables and ensures required directories exist.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment."""
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "text-embedding-3-large")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Paths
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    
    # Retrieval params
    TOP_K: int = int(os.getenv("TOP_K", "12"))
    CLUSTERS: int = int(os.getenv("CLUSTERS", "3"))
    
    # Chunking params
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "600"))  # target tokens
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "90"))  # overlap tokens


settings = Settings()


def ensure_directories():
    """Create required directories if they don't exist."""
    Path(settings.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

