from src.ingest.loader.arxiv_loader import download_arxiv_papers
from src.ingest.processor import process_pdf
from src.ingest.vector_store import init_collection, upsert_chunks
from src.ingest.config import settings
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pipeline():
    logger.info("Starting pipeline...")
    init_collection()

    pdf_paths = download_arxiv_papers(
        query=settings.QUERY,
        max_docs=5,
        save_dir=settings.RAW_PAPERS_DIR
    )

    all_chunks = []
    for pdf_path in pdf_paths:
        paper_id = Path(pdf_path).stem
        logger.info(f"Processing {paper_id}")
        chunks = process_pdf(pdf_path, paper_id)
        all_chunks.extend(chunks)

    logger.info(f"Upserting {len(all_chunks)} chunks...")
    upsert_chunks(all_chunks)
    logger.info("Pipeline complete!")