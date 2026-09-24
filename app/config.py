"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Central configuration — loaded from .env file and environment variables."""

    # OpenAI
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Retrieval
    top_k: int = 5
    similarity_threshold: float = 0.3

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "contracts"

    # Query log
    query_log_db: str = "./query_log.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 100

    # Paths
    contracts_dir: str = "./sample_contracts"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Singleton
settings = Settings()
