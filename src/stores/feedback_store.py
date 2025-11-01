from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from src.embeddings.embedder import embed_text
from config import settings
from uuid import uuid4
import logging

client = QdrantClient(url=settings.QDRANT_URL)
logger = logging.getLogger(__name__)

def init_feedback():
    if not client.collection_exists(collection_name=settings.QDRANT_FEEDBACK):
        client.create_collection(
            collection_name=settings.QDRANT_FEEDBACK,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def store_feedback(query: str, correction: str):
    """
    Stores user feedback in the Qdrant collection.

    Args:
        query (str): The original query string.
        correction (str): The user's correction or feedback.
    """
    vector = embed_text(query)
    points = PointStruct(
        id=str(uuid4()),
        vector=vector,
        payload={"correction": correction}
    )
    client.upsert(
        collection_name=settings.QDRANT_FEEDBACK,
        points=points,
        wait=True
    )