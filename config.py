from pathlib import Path
from pydantic_settings import BaseSettings
from enum import Enum
from typing import Optional
import os
from dotenv import load_dotenv

# IMPORTANT: Load .env file before anything else
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
    NARRATIVE_TEXT = "NarrativeText"
    TITLE = "Title"
    TEXT = "Text"
    LIST_ITEM = "ListItem"
    ABSTRACT = "Abstract"
    UNCATEGORIZED = "UncategorizedText"
    FIGURECAPTION = "FigureCaption"
    FORMULA = "Formula"
    CODESNIPPET = "CodeSnippet"