from pathlib import Path
from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file before anything else
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings for the ingestion process.
    """
    # Paths
    RAW_PAPERS_DIR: Path = Path("data/raw_papers")
    PROCESSED_DIR: Path = Path("data/processed")
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    VECTOR_COLLECTION: str = "arxiv_multimodal"
    FEEDBACK_COLLECTION: str = "feedback"

    # Models
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SUMMARIZER_MODEL: str = "facebook/bart-large-cnn"
    CAPTIONER_MODEL: str = "Salesforce/blip-image-captioning-large"
    LLM_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct"
    LLM_TASK: str = "text-generation"
    LLM_MAX_NEW_TOKENS: int = 8192

    # SUMMARIZATION PARAMETERS 
    CHUNK_SIZE: int = 3000
    CHUNK_OVERLAP: int = 100
    BASE_MAX: int = 130
    BASE_MIN: int = 30

    MAX_PAPERS: int = 10
    QUERY: str = "LLM agents"

    # API KEYS - Load from environment
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_TRACING_V2: bool = False

    # Monitoring
    METRICS_LOG_FILE: Path = Path("data/metrics_log.jsonl")
    ENABLE_LANGSMITH: bool = False

    # Voice settings
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    TTS_LANGUAGE: str = "en"
    ENABLE_VOICE_BY_DEFAULT: bool = False

    # Monitoring
    METRICS_LOG_FILE: Path = Path("data/metrics_log.jsonl")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()

# CRITICAL: Set environment variables for libraries that read from os.environ
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
if settings.HUGGINGFACEHUB_API_TOKEN:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = settings.HUGGINGFACEHUB_API_TOKEN
if settings.GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
if settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
if settings.LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

class TextCategory(str, Enum):
    """
    Enum for different types of document chunks.
    """
    NARRATIVE_TEXT = "NarrativeText"
    TITLE = "Title"
    TEXT = "Text"
    LIST_ITEM = "ListItem"
    ABSTRACT = "Abstract"
    UNCATEGORIZED = "UncategorizedText"
    FIGURECAPTION = "FigureCaption"
    FORMULA = "Formula"
    CODESNIPPET = "CodeSnippet"