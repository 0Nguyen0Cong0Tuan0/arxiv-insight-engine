import chromadb
from chromadb.config import Settings as ChromaSettings
from src.embeddings.embedder import embed_text
from config import settings
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

# Use the same client as vector_store
chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=ChromaSettings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

def init_feedback():
    """
    Initialize or get the feedback collection in ChromaDB.
    """
    try:
        collection = chroma_client.get_collection(name=settings.FEEDBACK_COLLECTION)
        logger.info(f"Feedback collection '{settings.FEEDBACK_COLLECTION}' already exists.")
    except Exception:
        collection = chroma_client.create_collection(
            name=settings.FEEDBACK_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Created feedback collection '{settings.FEEDBACK_COLLECTION}'.")
    return collection

def store_feedback(query: str, correction: str):
    """
    Stores user feedback in the ChromaDB collection.
    """
    collection = chroma_client.get_collection(name=settings.FEEDBACK_COLLECTION)
    vector = embed_text(query)
    
    feedback_id = str(uuid4())
    
    collection.add(
        ids=[feedback_id],
        embeddings=[vector],
        documents=[query],
        metadatas=[{"correction": correction}]
    )
    
    logger.info(f"Stored feedback for query: {query[:50]}...")

def get_feedback(query: str, n_results: int = 5):
    """
    Retrieve similar feedback for a given query.
    """
    collection = chroma_client.get_collection(name=settings.FEEDBACK_COLLECTION)
    vector = embed_text(query)
    
    results = collection.query(
        query_embeddings=[vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    return results