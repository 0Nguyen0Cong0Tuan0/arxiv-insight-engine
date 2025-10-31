from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal, Optional

class Settings(BaseSettings):
    """
    Configuration settings for the ingestion process.
    """
    # Paths
    RAW_PAPERS_DIR: Path = Path("../../data/raw_papers")
    PROCESSED_DIR: Path = Path("../../data/processed")
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "arxiv_multimodal"

    # Models
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SUMMARIZER_MODEL: str = "facebook/bart-large-cnn"
    CAPTIONER_MODEL: str = "Salesforce/blip-image-captioning-large"

    # SUMMARIZATION PARAMETERS 
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 100
    BASE_MAX: int = 200
    BASE_MIN: int = 30

    MAX_PAPERS: int = 10
    QUERY: str = "LLM agents"

    # API KEYS
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()