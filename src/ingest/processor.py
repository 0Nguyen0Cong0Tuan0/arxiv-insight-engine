from src.ingest.parser.multimodal_parser import parse_pdf
from src.ingest.tools.summarizer import Summarizer
from src.ingest.tools.image_captioner import ImageCaptioner
from src.ingest.models.document import DocumentChunk, ChunkType
from uuid import uuid4

def process_pdf(pdf_path: str, paper_id: str):
    """
    Processes a PDF file to extract text, tables, and figures,
    generates summaries and captions, and returns structured document chunks.

    Args:
        pdf_path (str): Path to the PDF file.
        paper_id (str): Identifier for the paper.

    Returns:
        List of DocumentChunk objects.
    """
    elements, texts, tables = parse_pdf(pdf_path)

    summarizer = Summarizer()
    captioner = ImageCaptioner()

    # Extract images
    all_images_b64 = captioner.extract_base64_images(elements)
    image_captions = captioner.caption_images(all_images_b64)

    # Summarize texts and tables
    raw_texts = [getattr(t, "text", "").strip() for t in texts if getattr(t, "text", "").strip()]
    raw_htmls = [getattr(t.metadata, "text_as_html", "").strip() for t in tables if hasattr(t.metadata, "text_as_html")]

    text_summaries = summarizer.summarize_texts(raw_texts)
    table_summaries = summarizer.summarize_texts(raw_htmls)

    # Build chunks
    chunks = []
    img_idx = 0
    for i, elem in enumerate(elements):
        chunk_id = f"{paper_id}_{i}"
        if "NarrativeText" in str(type(elem)):
            if raw_texts:
                chunks.append(DocumentChunk(
                    paper_id=paper_id, chunk_id=chunk_id, type=ChunkType.TEXT,
                    content=elem.text, summary=text_summaries.pop(0) if text_summaries else ""
                ))
        elif "Table" in str(type(elem)):
            chunks.append(DocumentChunk(
                paper_id=paper_id, chunk_id=chunk_id, type=ChunkType.TABLE,
                content=elem.text, summary=table_summaries.pop(0) if table_summaries else "",
                metadata={"html": elem.metadata.text_as_html or ""}
            ))
        elif "Image" in str(type(elem)):
            if img_idx < len(image_captions):
                chunks.append(DocumentChunk(
                    paper_id=paper_id, chunk_id=chunk_id, type=ChunkType.FIGURE,
                    content="", caption=image_captions[img_idx],
                    image_path=f"{paper_id}_fig_{img_idx}.png"
                ))
                img_idx += 1
    return chunks