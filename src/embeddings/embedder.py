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

import asyncio
from concurrent.futures import ThreadPoolExecutor

# Create a thread pool for embedding operations
executor = ThreadPoolExecutor(max_workers=4)

async def embed_text(text: str) -> List[float]:
    """
    Generate embeddings asynchronously to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, 
        embedder.embed_query, 
        text
    )

async def embed_documents(texts: list) -> List[List[float]]:
    """
    Generate document embeddings asynchronously.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor, 
        embedder.embed_documents, 
        texts
    )