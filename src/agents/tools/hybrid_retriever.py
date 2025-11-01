from langchain_community.retrievers import BM25Retriever
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from typing import List, Any
from langchain_core.documents import Document
from src.embeddings.embedder import embedder
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = QdrantClient(url=settings.QDRANT_URL)
qdrant = QdrantVectorStore(client, settings.QDRANT_VECTOR_STORE, embedder)

class EnsembleRetriever:
    def __init__(self, retrievers: List[Any], weights: List[float] = None):
        self.retrievers = [r for r in retrievers if r]  # Filter out None/empty retrievers
        self.weights = weights or [1.0 / len(self.retrievers) for _ in self.retrievers]
        if len(self.weights) != len(self.retrievers):
            raise ValueError("Number of weights must match number of retrievers")
        if not self.retrievers:
            raise ValueError("At least one retriever must be provided")

    @classmethod
    def from_qdrant(cls) -> "EnsembleRetriever":
        """Initialize a hybrid retriever using Qdrant data."""
        # Fetch documents from Qdrant for BM25 corpus
        docs = qdrant.similarity_search("placeholder", k=100)  # Broad query to get corpus
        bm25_texts = [d.page_content for d in docs if d.page_content and d.page_content.strip()]

        if not bm25_texts:
            logger.warning("No valid text found in Qdrant. Using vector retriever only.")
            return cls(retrievers=[qdrant.as_retriever(search_kwargs={"k": 10})], weights=[1.0])

        bm25 = BM25Retriever.from_texts(bm25_texts)
        bm25.k = 5
        vector_retriever = qdrant.as_retriever(search_kwargs={"k": 10})

        return cls(retrievers=[vector_retriever, bm25], weights=[0.7, 0.3])

    def retrieve(self, query: str, k: int = 10) -> List[Document]:
        """Perform hybrid retrieval using the user query."""
        results = []
        for retriever, weight in zip(self.retrievers, self.weights):
            try:
                docs = retriever.invoke(query)
                for rank, doc in enumerate(docs, 1):
                    score = weight / rank
                    results.append((doc, score))
            except Exception as e:
                logger.warning(f"Retriever failed: {e}. Skipping this retriever.")

        if not results:
            logger.warning("No documents retrieved from any retriever.")
            return []

        # Aggregate and rank results
        doc_scores = {}
        for doc, score in results:
            doc_id = doc.metadata.get("id", id(doc))  # Use unique identifier
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0.0}
            doc_scores[doc_id]["score"] += score

        # Sort by score and return top k
        ranked_docs = [
            item["doc"] for item in sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
        ]
        return ranked_docs[:k]