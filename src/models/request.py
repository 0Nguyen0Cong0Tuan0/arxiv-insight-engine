from pydantic import BaseModel
from typing import List, Optional

class ArxivSearchRequest(BaseModel):
    query: str
    max_results: int = 20

class IngestPapersRequest(BaseModel):
    paper_ids: List[str]

class QueryRequest(BaseModel):
    query: str
    image_base64: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    sources: List[dict] = []
    image_caption: Optional[str] = None