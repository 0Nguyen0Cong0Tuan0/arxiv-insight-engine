from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from src.ingest.config import settings
from src.ingest.embeddings.embedder import embedder
from uuid import uuid4
import logging

client = QdrantClient(url=settings.QDRANT_URL)
logger = logging.getLogger(__name__)

def init_collection():
    if not client.collection_exists(collection_name=settings.QDRANT_COLLECTION):
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def upsert_chunks(chunks):
    """
    Embeds chunks and upserts them into the Qdrant collection.

    Args:
        chunks (list): List of chunk objects to be embedded and upserted.
    """

    if not chunks:
        logger.warning("No chunks provided to upsert. Skipping.")
        return
    
    points = []
    for chunk in chunks:
        text = chunk.summary or chunk.content or chunk.caption or ""
        vector = embedder.embed_query(text)
        payload, _ = chunk.to_qdrant_payload(vector)

        points.append(PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload=payload
        ))

    client.upsert(
        collection_name=settings.QDRANT_COLLECTION, 
        points=points,
        wait=True
    )