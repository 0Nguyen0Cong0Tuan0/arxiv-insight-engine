from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from uuid import uuid4
from ingest.u_embedder import embed_text
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))

COLLECTION_NAME = "arxiv_multimodal"
VECTOR_SIZE = 384 

def init_collection():
    if not client.has_collection(collection_name=COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f'Create collection: {COLLECTION_NAME}')

def upsert_chunks(chunks: list, paper_id: str):
    points = []
    for i, chunk in enumerate(chunks):
        text = chunk.text
        vector = embed_text(text) 