import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import base64
import logging
import tempfile
import time
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from contextlib import asynccontextmanager

from config import settings
from typing import List, Optional
from src.ingest.pipeline import process_single_pdf
from src.ingest.loader.arxiv_loader import search_arxiv_papers, download_single_arxiv_paper
from src.agents.graph import app as agent_app
from src.agents.tools.image_captioner import ImageCaptioner
from src.stores.vector_store import init_collection, get_collection
from src.models.request import ArxivSearchRequest, IngestPapersRequest, QueryRequest, QueryResponse

# Import voice and monitoring components
from src.app.voice_handler import voice_handler
from src.monitoring.metrics_tracker import metrics_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up ArXiv Insight Engine...")
    yield
    # Shutdown actions
    logger.info("Shutting down ArXiv Insight Engine...")

# Initialize FastAPI
app = FastAPI(title="ArXiv Insight Engine", version="1.0.0", lifespan=lifespan)

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
    """Upload PDF files and process them into the vector store."""
    start_time = time.time()
    
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
        
        # Track metrics
        latency = time.time() - start_time
        metrics_tracker.record_operation(
            operation="pdf_upload",
            latency=latency,
            success=True,
            tokens_used=sum(f["chunks_added"] for f in processed_files) * 100,
            metadata={"files_count": len(processed_files)}
        )
        
        return {
            'success': True,
            'message': f"Processed {len(processed_files)} files.",
            'files': processed_files
        }

    except Exception as e:
        logger.error(f"Error uploading PDFs: {e}")
        metrics_tracker.record_operation(
            operation="pdf_upload",
            latency=time.time() - start_time,
            success=False,
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Error processing uploaded PDFs.")

# ArXiv Search Endpoints
@app.post("/api/arxiv/search")
async def search_arxiv(request: ArxivSearchRequest):
    """Search ArXiv for papers without downloading them."""
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
    """Download and ingest selected ArXiv papers."""
    start_time = time.time()
    
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
        
        # Track metrics
        latency = time.time() - start_time
        metrics_tracker.record_operation(
            operation="arxiv_ingest",
            latency=latency,
            success=len(processed) > 0,
            tokens_used=sum(p["chunks_added"] for p in processed) * 100,
            metadata={
                "requested": len(request.paper_ids),
                "successful": len(processed),
                "failed": len(failed)
            }
        )
        
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
    """Process a text query using the agent workflow."""
    start_time = time.time()
    
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
        
        # Track metrics
        latency = time.time() - start_time
        metrics_tracker.record_operation(
            operation="text_query",
            latency=latency,
            success=True,
            tokens_used=len(request.query) // 4 + len(result.get("synthesis", "")) // 4,
            metadata={
                "route": result.get("route", "unknown"),
                "chunks_retrieved": len(result.get("retrieved_chunks", [])),
                "has_image": request.image_base64 is not None
            }
        )
        
        return QueryResponse(
            response=result.get("synthesis", "No response generated"),
            sources=sources,
            image_caption=image_caption
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        metrics_tracker.record_operation(
            operation="text_query",
            latency=time.time() - start_time,
            success=False,
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/query/image")
async def query_image(
    query: str = Form(...),
    image: UploadFile = File(...)
):
    """Process a query with an uploaded image."""
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

@app.post("/api/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...)
):
    """
    Transcribe audio file to text using Whisper.
    """
    start_time = time.time()
    
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe
        transcribed_text, error = voice_handler.transcribe_audio(tmp_path)
        
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        # Track metrics
        latency = time.time() - start_time
        metrics_tracker.record_operation(
            operation="stt",
            latency=latency,
            success=True,
            tokens_used=len(transcribed_text) // 4,
            metadata={
                "audio_format": Path(audio.filename).suffix,
                "text_length": len(transcribed_text)
            }
        )
        
        return {
            "success": True,
            "text": transcribed_text,
            "latency": latency
        }
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        metrics_tracker.record_operation(
            operation="stt",
            latency=time.time() - start_time,
            success=False,
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/voice/synthesize")
async def synthesize_speech(
    text: str = Form(...), 
    lang: str = Form("en")
):
    """
    Convert text to speech using gTTS.
    """
    start_time = time.time()
    
    try:
        # Generate speech
        audio_bytes, error = voice_handler.text_to_speech(text, lang=lang)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        # Track metrics
        latency = time.time() - start_time
        metrics_tracker.record_operation(
            operation="tts",
            latency=latency,
            success=True,
            tokens_used=len(text),
            metadata={
                "text_length": len(text),
                "language": lang
            }
        )
        
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    
    except Exception as e:
        logger.error(f"TTS error: {e}")
        metrics_tracker.record_operation(
            operation="tts",
            latency=time.time() - start_time,
            success=False,
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@app.post("/api/voice/query")
async def voice_query(audio: UploadFile = File(...)):
    """Complete voice workflow: audio → transcribe → query → synthesize → audio"""
    start_time = time.time()
    
    try:
        # Transcribe audio to text
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        transcribed_text, transcribe_error = voice_handler.transcribe_audio(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        
        if transcribe_error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcribe_error}")
        
        # Process query through agent
        initial_state = {
            "query": transcribed_text,
            "messages": [],
            "retrieved_chunks": [],
            "summaries": [],
            "figure_insights": [],
            "synthesis": "",
            "verified": True,
            "feedback": ""
        }
        
        config = {"configurable": {"thread_id": "voice_session"}}
        result = await agent_app.ainvoke(initial_state, config)
        response_text = result.get("synthesis", "No response generated")
        
        # Convert response to speech
        audio_bytes, tts_error = voice_handler.text_to_speech(response_text)
        
        if tts_error:
            raise HTTPException(status_code=500, detail=f"TTS failed: {tts_error}")
        
        # Track complete workflow
        latency = time.time() - start_time
        metrics_tracker.record_operation(
            operation="voice_query_complete",
            latency=latency,
            success=True,
            tokens_used=len(transcribed_text) // 4 + len(response_text) // 4,
            metadata={
                "transcribed_length": len(transcribed_text),
                "response_length": len(response_text),
                "route": result.get("route", "unknown")
            }
        )
        
        # Return both text and audio
        return {
            "success": True,
            "transcribed_text": transcribed_text,
            "response_text": response_text,
            "audio_base64": base64.b64encode(audio_bytes).decode('utf-8'),
            "latency": latency,
            "route": result.get("route", "unknown")
        }
    
    except Exception as e:
        logger.error(f"Voice query error: {e}")
        metrics_tracker.record_operation(
            operation="voice_query_complete",
            latency=time.time() - start_time,
            success=False,
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Voice query failed: {str(e)}")

@app.get("/api/metrics/summary")
async def get_metrics_summary(hours: int = 24):
    """Get summary metrics for the last N hours"""
    try:
        stats = metrics_tracker.get_summary_stats(hours=hours)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")

@app.get("/api/metrics/errors")
async def get_recent_errors(limit: int = 10):
    """Get recent error records"""
    try:
        errors = metrics_tracker.get_recent_errors(limit=limit)
        return {
            "success": True,
            "errors": errors,
            "count": len(errors)
        }
    except Exception as e:
        logger.error(f"Error getting errors: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving errors")

@app.get("/api/metrics/export")
async def export_metrics():
    """Export all metrics to JSON file"""
    try:
        output_path = PROJECT_ROOT / "data" / f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        metrics_tracker.export_metrics(str(output_path))
        
        return {
            "success": True,
            "message": f"Metrics exported to {output_path.name}",
            "path": str(output_path)
        }
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error exporting metrics")

@app.get("/api/metrics/dashboard")
async def metrics_dashboard(hours: int = 24):
    """
    Get comprehensive dashboard data including:
    - Summary stats
    - Operation breakdown
    - Recent errors
    - Time-series data (simplified)
    """
    try:
        stats = metrics_tracker.get_summary_stats(hours=hours)
        errors = metrics_tracker.get_recent_errors(limit=5)
        
        # Calculate additional insights
        ops_breakdown = stats.get("operations_breakdown", {})
        
        # Top slowest operations
        slowest_ops = sorted(
            [(name, data["avg_latency"]) for name, data in ops_breakdown.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Most expensive operations
        most_expensive = sorted(
            [(name, data["total_cost"]) for name, data in ops_breakdown.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "success": True,
            "summary": {
                "total_operations": stats["total_operations"],
                "success_rate": stats["success_rate"],
                "avg_latency": stats["avg_latency"],
                "total_cost": stats["total_cost"],
                "time_window_hours": hours
            },
            "operations": ops_breakdown,
            "recent_errors": errors,
            "insights": {
                "slowest_operations": [{"name": name, "latency": lat} for name, lat in slowest_ops],
                "most_expensive": [{"name": name, "cost": cost} for name, cost in most_expensive]
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard data")


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

# @app.get("/")
# async def startup_event():
#     """Log startup information"""
#     logger.info("=" * 50)
#     logger.info("ArXiv Insight Engine Started")
#     logger.info(f"Voice Assistant: Enabled")
#     logger.info(f"Metrics Tracking: Enabled")
#     logger.info(f"Whisper Model: {settings.WHISPER_MODEL if hasattr(settings, 'WHISPER_MODEL') else 'base'}")
#     logger.info("=" * 50)