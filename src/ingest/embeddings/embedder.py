from typing import List
from langchain_huggingface import HuggingFaceEmbeddings

embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def embed_text(text: str) -> List[float]:
    """
    Generate embeddings for the given text using HuggingFace model.
    """
    return embedder.embed_query(text)

def embed_documents(texts: list) -> List[List[float]]:
    """
    Generate embeddings for a list of documents.
    """
    return embedder.embed_documents(texts)