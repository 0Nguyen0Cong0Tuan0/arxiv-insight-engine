from pydantic import BaseModel
from typing import List, Optional

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from config import settings

class ArxivSearchRequest(BaseModel):
    query: str
    max_results: int = settings.MAX_PAPERS

class IngestPapersRequest(BaseModel):
    paper_ids: List[str]

class QueryRequest(BaseModel):
    query: str
    image_base64: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    sources: List[dict] = []
    image_caption: Optional[str] = None