from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer, util

model_name = "sentence-transformers/all-MiniLM-L6-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}

embedder = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

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