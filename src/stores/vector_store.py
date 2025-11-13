import chromadb
from chromadb.config import Settings as ChromaSettings
from src.embeddings.embedder import embed_text, embed_documents
from config import settings
import logging
from typing import List

logger = logging.getLogger(__name__)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=ChromaSettings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

def init_collection():
    """
    Initialize or get the vector collection in ChromaDB.
    """
    try:
        collection = chroma_client.get_collection(name=settings.VECTOR_COLLECTION)
        logger.info(f"Collection '{settings.VECTOR_COLLECTION}' already exists.")
    except Exception:
        collection = chroma_client.create_collection(
            name=settings.VECTOR_COLLECTION,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        logger.info(f"Created collection '{settings.VECTOR_COLLECTION}'.")
    return collection

def get_collection():
    """
    Get the existing vector collection.
    """
    return chroma_client.get_collection(name=settings.VECTOR_COLLECTION)

def upsert_chunks(chunks):
    """
    Embeds chunks and upserts them into the ChromaDB collection.
    """
    if not chunks:
        logger.warning("No chunks provided to upsert. Skipping.")
        return
    
    collection = get_collection()
    
    # Prepare data for ChromaDB
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        text = chunk.content or ""
        vector = embed_text(text)
        payload, _ = chunk.to_qdrant_payload(vector)
        
        # ChromaDB requires string IDs
        ids.append(chunk.chunk_id)
        embeddings.append(vector)
        documents.append(text)
        metadatas.append(payload)
    
    # Upsert to ChromaDB (handles both insert and update)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    logger.info(f"Upserted {len(chunks)} chunks to ChromaDB.")

def query_collection(query_text: str, n_results: int = 10):
    """
    Query the collection with a text query.
    """
    collection = get_collection()
    query_embedding = embed_text(query_text)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    return results

def get_all_documents():
    """
    Retrieve all documents from the collection.
    Useful for BM25 indexing.
    """
    collection = get_collection()
    
    # Get all documents (ChromaDB has a limit, so we page through)
    all_docs = []
    offset = 0
    limit = 1000
    
    while True:
        results = collection.get(
            limit=limit,
            offset=offset,
            include=["documents", "metadatas"]
        )
        
        if not results["ids"]:
            break
            
        all_docs.extend([
            {
                "id": id_,
                "document": doc,
                "metadata": meta
            }
            for id_, doc, meta in zip(
                results["ids"],
                results["documents"],
                results["metadatas"]
            )
        ])
        
        offset += limit
        
        if len(results["ids"]) < limit:
            break
    
    return all_docs

def delete_collection():
    """
    Delete the entire collection. Use with caution!
    """
    try:
        chroma_client.delete_collection(name=settings.VECTOR_COLLECTION)
        logger.info(f"Deleted collection '{settings.VECTOR_COLLECTION}'.")
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")