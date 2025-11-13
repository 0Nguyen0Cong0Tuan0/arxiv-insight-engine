import sys
from pathlib import Path 
from typing import List
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from config import TextCategory

class DocumentChunk(BaseModel):
    """
    Model representing a chunk of a document.
    """
    paper_id: str
    chunk_id: str
    type: TextCategory
    content: str
    metadata: dict = {}

    def to_qdrant_payload(self, vector: List[float]) -> dict:
        """
        Converts the DocumentChunk to a Qdrant payload dictionary.
        """
        return {
            "paper_id": self.paper_id,
            "chunk_id": self.chunk_id,
            "type": self.type.value,
            "content": self.content,
            **self.metadata
        }, vector