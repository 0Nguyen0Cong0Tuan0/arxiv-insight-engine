from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from typing import List, Any
from src.embeddings.embedder import embedder
from config import settings
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings as ChromaSettings

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=ChromaSettings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Initialize LangChain Chroma wrapper
chroma_langchain = Chroma(
    client=chroma_client,
    collection_name=settings.VECTOR_COLLECTION,
    embedding_function=embedder
)

class EnsembleRetriever:
    def __init__(self, retrievers: List[Any], weights: List[float] = None):
        self.retrievers = [r for r in retrievers if r]
        self.weights = weights or [1.0 / len(self.retrievers) for _ in self.retrievers]
        if len(self.weights) != len(self.retrievers):
            raise ValueError("Number of weights must match number of retrievers")

    def get_hybrid_retriever(self, corpus: List[str] = None) -> "EnsembleRetriever":
        """
        Initialize a hybrid retriever combining vector and BM25 retrievers.
        :param corpus: Optional list of texts for BM25. If None, use ChromaDB documents.
        """
        # Vector retriever
        vector_retriever = chroma_langchain.as_retriever(
            search_kwargs={"k": 10}
        )

        # BM25 retriever
        if corpus is None:
            print(f"Fetching all documents from ChromaDB for BM25 index...")
            
            # Get all documents from ChromaDB
            collection = chroma_client.get_collection(name=settings.VECTOR_COLLECTION)
            
            # Fetch documents in batches
            all_docs = []
            offset = 0
            limit = 1000
            
            while True:
                results = collection.get(
                    limit=limit,
                    offset=offset,
                    include=["documents"]
                )
                
                if not results["ids"]:
                    break
                
                all_docs.extend(results["documents"])
                offset += limit
                
                if len(results["ids"]) < limit:
                    break
            
            bm25_texts = [doc for doc in all_docs if doc and doc.strip()]
        else:
            bm25_texts = [text for text in corpus if text and text.strip()]

        if not bm25_texts:
            print("Warning: No valid text for BM25. Falling back to vector retriever only.")
            return EnsembleRetriever(retrievers=[vector_retriever], weights=[1.0])

        print(f"Initializing BM25Retriever with {len(bm25_texts)} documents.")
        bm25 = BM25Retriever.from_texts(bm25_texts)
        bm25.k = 5

        return EnsembleRetriever(
            retrievers=[vector_retriever, bm25],
            weights=[0.7, 0.3]
        )

    def retrieve(self, query: str, k: int = 10) -> List[Document]:
        """
        Perform hybrid retrieval using the user query.
        :param query: The user query to search for.
        :param k: Number of results to return.
        :return: List of ranked documents.
        """
        results = []
        for retriever, weight in zip(self.retrievers, self.weights):
            docs = retriever.invoke(query)
            for rank, doc in enumerate(docs, 1):
                score = weight / (rank + 60)
                results.append((doc, score))

        doc_scores = {}
        for doc, score in results:
            doc_id = doc.metadata.get("chunk_id")

            if not doc_id:
                doc_id = doc.page_content
                
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0.0}
            doc_scores[doc_id]["score"] += score

        ranked_docs = [
            item["doc"] for item in sorted(
                doc_scores.values(),
                key=lambda x: x["score"],
                reverse=True
            )
        ]
        return ranked_docs[:k]