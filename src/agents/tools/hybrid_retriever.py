from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient
from src.ingest.embeddings.embedder import embedder

from src.ingest.config import settings

client = QdrantClient(url=settings.QDRANT_URL)
qdrant = Qdrant(client, settings.QDRANT_COLLECTION, embedder)

def get_hybrid_retriever():
    """
    Get a hybrid retriever combining vector and BM25 retrievers.
    """
    # Vector retriever
    vector_retriever = qdrant.as_retriever(search_kwargs={"k": 10})

    # BM25 on content
    docs = qdrant.similarity_search("test", k=100)
    bm25 = BM25Retriever.from_texts([d.page_content for d in docs])
    bm25.k = 5

    return EnsembleRetriever(
        retrievers=[vector_retriever, bm25],
        weights=[0.7, 0.3]
    )
