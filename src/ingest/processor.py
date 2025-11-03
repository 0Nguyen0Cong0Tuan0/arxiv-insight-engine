import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from config import TextCategory
from src.ingest.parser.multimodal_parser import parse_pdf
from src.models.document import DocumentChunk, ChunkType

def process_pdf(pdf_path: str, paper_id: str):
    """
    Processes a PDF file to extract text, tables, and figures,
    and returns structured document chunks.

    Args:
        pdf_path (str): Path to the PDF file.
        paper_id (str): Identifier for the paper.

    Returns:
        List of DocumentChunk objects.
    """
    elements = parse_pdf(pdf_path)

    # Build chunks
    chunks = []

    TEXT_CATEGORIES = {
        TextCategory.NARRATIVE_TEXT,
        TextCategory.TITLE,
        TextCategory.TEXT,
        TextCategory.LIST_ITEM,
        TextCategory.ABSTRACT,
        TextCategory.UNCATEGORIZED,
        TextCategory.FIGURECAPTION,
        TextCategory.FORMULA,
        TextCategory.CODESNIPPET
    }
    
    for i, composite_elem in enumerate(elements):
        try:
            orig_elements = composite_elem.metadata.orig_elements
            if not isinstance(orig_elements, list):
                continue
        except AttributeError:
            continue

        for j, elem in enumerate(orig_elements):
            chunk_id = f"{paper_id}_{i}_{j}" 
            
            category = getattr(elem, "category", "")

            if category in TEXT_CATEGORIES:
                chunks.append(DocumentChunk(
                    paper_id=paper_id, chunk_id=chunk_id, type=ChunkType.TEXT,
                    content=getattr(elem, "text", ""), 
                ))
            
            elif category == "Table":
                chunks.append(DocumentChunk(
                    paper_id=paper_id, chunk_id=chunk_id, type=ChunkType.TABLE,
                    content=getattr(elem, "text", ""), 
                    metadata={"html": getattr(elem.metadata, "text_as_html", "") or ""}
                ))

            elif category == "Image":
                chunks.append(DocumentChunk(
                    paper_id=paper_id, chunk_id=chunk_id, type=ChunkType.FIGURE,
                    content=getattr(elem.metadata, "image_base64", ""),
                ))
    
    return chunks