import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import base64
import logging

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from config import settings
from typing import List, Optional
from src.ingest.pipeline import process_single_pdf
from src.ingest.loader.arxiv_loader import search_arxiv_papers, download_single_arxiv_paper
from src.agents.graph import app as agent_app
from src.agents.tools.image_captioner import ImageCaptioner
from src.stores.vector_store import init_collection, get_collection
from src.models.request import ArxivSearchRequest, IngestPapersRequest, QueryRequest, QueryResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="ArXiv Insight Engine", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize collections
init_collection()

# Serve static files
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "src/app/static")), name="static")

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    html_path = PROJECT_ROOT / "src/app/templates/index.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>ArXiv Insight Engine</h1><p>Frontend not found. Please create templates/index.html</p>"

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/stats")
async def get_stats():
    """Get collection statistics"""
    try:
        collection = get_collection()
        count = collection.count()
        
        # Estimate papers (rough estimate: 1 paper = ~150 chunks)
        papers_estimate = max(1, count // 150)
        
        return {
            "papers_count": papers_estimate,
            "chunks_count": count
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"papers_count": 0, "chunks_count": 0}
    
# Upload Endpoints
@app.post("/api/ingest/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """
    Upload PDF files and process them into the vector store.
    """
    try: 
        processed_files = []

        for file in files:
            if not file.filename.endswith(".pdf"):
                continue

            # Save file
            file_path = settings.RAW_PAPERS_DIR / file.filename
            settings.RAW_PAPERS_DIR.mkdir(parents=True, exist_ok=True)

            content = await file.read()
            file_path.write_bytes(content)

            # Process PDF
            paper_id = file_path.stem
            logger.info(f"Processing uploaded file: {file.filename} as paper ID: {paper_id}")

            chunks_count = await process_single_pdf(str(file_path), paper_id)

            processed_files.append({
                "filename": file.filename,
                "paper_id": paper_id,
                "chunks_added": chunks_count
            })
        
        return {
            'success': True,
            'message': f"Processed {len(processed_files)} files.",
            'files': processed_files
        }

    except Exception as e:
        logger.error(f"Error uploading PDFs: {e}")
        raise HTTPException(status_code=500, detail="Error processing uploaded PDFs.")

# ArXiv Search Endpoints
@app.post("/api/arxiv/search")
async def search_arxiv(request: ArxivSearchRequest):
    """
    Search ArXiv for papers without downloading them.
    """
    try:
        results = search_arxiv_papers(
            query=request.query,
            max_results=request.max_results
        )

        return {
            'success': True,
            'count': len(results),
            'results': results
        }

    except Exception as e:
        logger.error(f"Error searching ArXiv: {e}")
        raise HTTPException(status_code=500, detail="Error searching ArXiv.")

@app.post("/api/arxiv/ingest")
async def ingest_arxiv_papers(request: IngestPapersRequest):
    """
    Download and ingest selected ArXiv papers.
    """
    try:
        processed = []
        failed = []

        for paper_id in request.paper_ids:
            logger.info(f"Processing ArXiv paper: {paper_id}")
            pdf_path = download_single_arxiv_paper(paper_id, settings.RAW_PAPERS_DIR)

            if pdf_path:
                try:
                    chunks_count = await process_single_pdf(pdf_path, paper_id)

                    processed.append({
                        "paper_id": paper_id,
                        "chunks_added": chunks_count,
                        "status": "success"
                    })
                    logger.info(f"Successfully processed {paper_id}: {chunks_count} chunks")
                    
                except Exception as e:
                    logger.error(f"Error processing {paper_id}: {e}")
                    failed.append({
                        "paper_id": paper_id,
                        "error": str(e),
                        "status": "processing_failed"
                    })
            else:
                logger.warning(f"Failed to download {paper_id}")
                failed.append({
                    "paper_id": paper_id,
                    "error": "Download failed",
                    "status": "download_failed"
                })
        
        return {
            'success': len(processed) > 0,
            'message': f"Processed {len(processed)} papers successfully. {len(failed)} failed.",
            'papers': processed,
            'failed': failed,
            'total_requested': len(request.paper_ids),
            'successful': len(processed),
            'failed_count': len(failed)
        }
        
    except Exception as e:
        logger.error(f"Error in ingest endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error ingesting ArXiv papers: {str(e)}")


# Query Endpoints
@app.post("/api/query/text", response_model=QueryResponse)
async def query_text(request: QueryRequest):
    """
    Process a text query using the agent workflow.
    """
    try:
        # Prepare initial state
        initial_state = {
            "query": request.query,
            "messages": [],
            "retrieved_chunks": [],
            "summaries": [],
            "figure_insights": [],
            "synthesis": "",
            "verified": True,
            "feedback": ""
        }

        # Handle image if provided
        image_caption = None
        if request.image_base64:
            captioner = ImageCaptioner()
            image_caption = captioner.caption_images([request.image_base64])[0]
            initial_state["query"] = f"{request.query} [Image context: {image_caption}]"
        
        # Run the agent
        config = {
            "configurable": {
                "thread_id": "default"
            }
        }
        result = await agent_app.ainvoke(initial_state, config)

        # Extract sources
        sources = []
        if result.get("retrieved_chunks"):
            for chunk in result["retrieved_chunks"][:5]:
                sources.append({
                    "paper_id": chunk.metadata.get("paper_id", "Unknown"),
                    "content": chunk.page_content[:200] + "..."
                })
        
        return QueryResponse(
            response=result.get("synthesis", "No response generated"),
            sources=sources,
            image_caption=image_caption
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/query/image")
async def query_image(
    query: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Process a query with an uploaded image.
    """
    try:
        # Read and encode image
        image_content = await image.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        # Use the text query endpoint
        request = QueryRequest(
            query=query,
            image_base64=image_base64
        )
        
        return await query_text(request)
    
    except Exception as e:
        logger.error(f"Error processing image query: {e}")
        raise HTTPException(status_code=500, detail="Error processing image query.")
    
# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )