from loader.arxiv_loader import download_arxiv_papers
from processor import process_pdf
from config import settings
from pathlib import Path
import logging
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from stores.vector_store import init_collection, upsert_chunks

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

    if all_chunks:
        logger.info(f"Upserting {len(all_chunks)} chunks...")
        upsert_chunks(all_chunks)
    else:
        logger.warning("No chunks were extracted from the PDFs. Nothing to upsert.")
        
    logger.info("Pipeline complete!")