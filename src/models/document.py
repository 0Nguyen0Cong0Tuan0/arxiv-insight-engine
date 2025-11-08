from enum import Enum
from typing import List
from pydantic import BaseModel

class ChunkType(str, Enum):
    """
    Enum for different types of document chunks.
    """
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"

class DocumentChunk(BaseModel):
    """
    Model representing a chunk of a document.
    """
    paper_id: str
    chunk_id: str
    type: ChunkType
    content: str
    metadata: dict = {}

    def to_qdrant_payload(self, vector: List[float]) -> dict:
        """
        Converts the DocumentChunk to a Qdrant payload dictionary.

        Args:
            vector (List[float]): The embedding vector for the chunk.

        Returns:
            dict: The payload dictionary for Qdrant.
        """
        return {
            "paper_id": self.paper_id,
            "chunk_id": self.chunk_id,
            "type": self.type.value,
            "content": self.content,
            **self.metadata
        }, vector