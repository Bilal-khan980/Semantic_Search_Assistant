"""
REST API server for the document search backend.
Provides endpoints for document processing, search, and Readwise integration.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
import tempfile
import os
from pathlib import Path
import uuid

from main import DocumentSearchBackend

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Local Document Search API",
    description="Privacy-first semantic search for documents and Readwise highlights",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global backend instance
backend: Optional[DocumentSearchBackend] = None

# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20
    similarity_threshold: Optional[float] = 0.3

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    processing_time_ms: float

class ReadwiseImportRequest(BaseModel):
    markdown_content: str

class DocumentProcessingStatus(BaseModel):
    task_id: str
    status: str  # "processing", "completed", "error"
    progress: float
    message: str
    results: Optional[List[Dict[str, Any]]] = None

class StatsResponse(BaseModel):
    total_chunks: int
    document_chunks: int
    readwise_highlights: int
    unique_sources: int
    embedding_model: str
    embedding_dimension: int

# In-memory task storage (use Redis in production)
processing_tasks: Dict[str, DocumentProcessingStatus] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the backend on startup."""
    global backend
    try:
        backend = DocumentSearchBackend()
        await backend.initialize()
        logger.info("API server started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global backend
    if backend:
        await backend.cleanup()
        logger.info("API server shutdown complete")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Local Document Search API", "status": "running"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        stats = await backend.get_stats()
        return {
            "status": "healthy",
            "backend_initialized": backend is not None,
            "database_stats": stats
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search across all indexed documents and highlights."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")
    
    try:
        import time
        start_time = time.time()
        
        results = await backend.search(
            query=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=round(processing_time, 2)
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload and process multiple documents."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    processing_tasks[task_id] = DocumentProcessingStatus(
        task_id=task_id,
        status="processing",
        progress=0.0,
        message="Starting document processing..."
    )
    
    # Start background processing
    background_tasks.add_task(process_documents_background, task_id, files)
    
    return {"task_id": task_id, "message": "Document processing started"}

async def process_documents_background(task_id: str, files: List[UploadFile]):
    """Background task for processing documents."""
    try:
        # Save uploaded files temporarily
        temp_files = []
        for file in files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_files.append(temp_file.name)
        
        # Update progress callback
        async def progress_callback(progress: float, message: str):
            if task_id in processing_tasks:
                processing_tasks[task_id].progress = progress
                processing_tasks[task_id].message = message
        
        # Process documents
        results = await backend.process_documents(temp_files, progress_callback)
        
        # Update final status
        processing_tasks[task_id].status = "completed"
        processing_tasks[task_id].progress = 100.0
        processing_tasks[task_id].message = "Processing completed"
        processing_tasks[task_id].results = results
        
        # Cleanup temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        processing_tasks[task_id].status = "error"
        processing_tasks[task_id].message = str(e)

@app.get("/documents/processing/{task_id}")
async def get_processing_status(task_id: str):
    """Get the status of a document processing task."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return processing_tasks[task_id]

@app.post("/readwise/import")
async def import_readwise(
    background_tasks: BackgroundTasks,
    request: ReadwiseImportRequest
):
    """Import Readwise highlights from markdown content."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    processing_tasks[task_id] = DocumentProcessingStatus(
        task_id=task_id,
        status="processing",
        progress=0.0,
        message="Starting Readwise import..."
    )
    
    # Start background processing
    background_tasks.add_task(import_readwise_background, task_id, request.markdown_content)
    
    return {"task_id": task_id, "message": "Readwise import started"}

async def import_readwise_background(task_id: str, markdown_content: str):
    """Background task for importing Readwise data."""
    try:
        # Update progress callback
        async def progress_callback(progress: float, message: str):
            if task_id in processing_tasks:
                processing_tasks[task_id].progress = progress
                processing_tasks[task_id].message = message
        
        # Import highlights
        results = await backend.import_readwise_data(markdown_content, progress_callback)
        
        # Update final status
        processing_tasks[task_id].status = "completed"
        processing_tasks[task_id].progress = 100.0
        processing_tasks[task_id].message = "Import completed"
        processing_tasks[task_id].results = results
        
    except Exception as e:
        logger.error(f"Readwise import error: {e}")
        processing_tasks[task_id].status = "error"
        processing_tasks[task_id].message = str(e)

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get statistics about indexed documents."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")
    
    try:
        stats = await backend.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/suggestions")
async def get_search_suggestions(q: str):
    """Get search suggestions based on query prefix."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")
    
    if len(q) < 2:
        return {"suggestions": []}
    
    try:
        # For now, return some basic suggestions
        # This could be enhanced to use the search engine's suggestion functionality
        suggestions = await backend.search_engine.get_suggestions(q)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return {"suggestions": []}

@app.delete("/documents/clear")
async def clear_all_documents():
    """Clear all documents from the database (for testing)."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")
    
    try:
        # This would require implementing a clear method in the backend
        # For now, return a message
        return {"message": "Clear functionality not implemented yet"}
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
