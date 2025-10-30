from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from src.ingest.config import settings
from src.ingest.embeddings.embedder import embedder

client = QdrantClient(url=settings.QDRANT_URL)

def init_collection():
    if not client.has_collection(settings.QDRANT_COLLECTION):
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def upsert_chunks(chunks):
    from uuid import uuid4
    points = []
    for chunk in chunks:
        text = chunk.summary or chunk.content or chunk.caption or ""
        vector = embedder.embed_query(text)
        payload, _ = chunk.to_qdrant_payload(vector)
        points.append({
            "id": str(uuid4()),
            "vector": vector,
            "payload": payload
        })
    client.upsert(settings.QDRANT_COLLECTION, points)