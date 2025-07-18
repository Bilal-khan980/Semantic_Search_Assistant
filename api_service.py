"""
REST API server for the document search backend.
Provides endpoints for document processing, search, and Readwise integration.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
import tempfile
import os
from pathlib import Path
import uuid
import json
import time

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

# Mount static files for web interface
app.mount("/static", StaticFiles(directory="web"), name="static")

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
    folder_path: str

class ProcessDocumentsRequest(BaseModel):
    file_paths: List[str]

class FolderScanRequest(BaseModel):
    folder_path: str

class FolderAddRequest(BaseModel):
    folder_path: str

class IndexingStatusRequest(BaseModel):
    file_path: Optional[str] = None

class TriggerIndexingRequest(BaseModel):
    file_paths: List[str]

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
progress_subscribers: Dict[str, List] = {}  # task_id -> list of queues for SSE

async def notify_progress_subscribers(task_id: str, update: Dict[str, Any]):
    """Notify all SSE subscribers of a progress update."""
    if task_id in progress_subscribers:
        for queue in progress_subscribers[task_id]:
            try:
                await queue.put(update)
            except Exception as e:
                logger.error(f"Failed to notify subscriber: {e}")

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

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    try:
        # Try to serve the comprehensive React app first
        with open("web/app.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        try:
            # Fallback to basic interface
            with open("web/index.html", "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head><title>Semantic Search Assistant</title></head>
            <body>
                <h1>🔍 Semantic Search Assistant</h1>
                <p>✅ Backend is running successfully!</p>
                <p>📚 API Documentation: <a href="/docs">/docs</a></p>
                <p>🔧 System Status: <a href="/system/status">/system/status</a></p>
                <p>❤️ Health Check: <a href="/health">/health</a></p>
            </body>
            </html>
            """)

@app.get("/api")
async def api_status():
    """API status endpoint."""
    return {"message": "Local Document Search API", "status": "running"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        stats = await backend.get_stats()
        folder_manager_status = "not_available"
        if hasattr(backend, 'folder_manager'):
            folder_manager_status = {
                "connected_folders": backend.folder_manager.get_connected_folders(),
                "is_monitoring": backend.folder_manager.is_monitoring,
                "processed_files_count": len(backend.folder_manager.processed_files)
            }

        return {
            "status": "healthy",
            "backend_initialized": backend is not None,
            "database_stats": stats,
            "folder_manager": folder_manager_status
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status including new components."""
    try:
        if not backend:
            return {"status": "error", "message": "Backend not initialized"}

        status = await backend.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/process")
async def process_documents_from_paths(
    background_tasks: BackgroundTasks,
    request: ProcessDocumentsRequest
):
    """Process documents from file paths."""
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
    background_tasks.add_task(process_file_paths_background, task_id, request.file_paths)

    return {"task_id": task_id, "message": "Document processing started"}

async def process_file_paths_background(task_id: str, file_paths: List[str]):
    """Background task for processing documents from file paths."""
    try:
        # Update progress callback
        async def progress_callback(progress: float, message: str):
            if task_id in processing_tasks:
                processing_tasks[task_id].progress = progress
                processing_tasks[task_id].message = message

                # Notify SSE subscribers
                await notify_progress_subscribers(task_id, processing_tasks[task_id].dict())

        # Process documents
        results = await backend.process_documents(file_paths, progress_callback)

        # Update final status
        processing_tasks[task_id].status = "completed"
        processing_tasks[task_id].progress = 100.0
        processing_tasks[task_id].message = "Processing completed"
        processing_tasks[task_id].results = results

    except Exception as e:
        logger.error(f"Document processing error: {e}")
        processing_tasks[task_id].status = "error"
        processing_tasks[task_id].message = str(e)

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

                # Notify SSE subscribers
                await notify_progress_subscribers(task_id, processing_tasks[task_id].dict())
        
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

@app.get("/process/status/{task_id}")
async def get_process_status(task_id: str):
    """Get the status of a document processing task (alternative endpoint)."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return processing_tasks[task_id]

@app.get("/documents/processing/{task_id}/stream")
async def stream_processing_status(task_id: str):
    """Stream real-time processing status updates via Server-Sent Events."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_stream():
        # Create a queue for this subscriber
        queue = asyncio.Queue()

        # Add to subscribers
        if task_id not in progress_subscribers:
            progress_subscribers[task_id] = []
        progress_subscribers[task_id].append(queue)

        try:
            # Send initial status
            initial_status = processing_tasks[task_id]
            yield f"data: {json.dumps(initial_status.dict())}\n\n"

            # Stream updates
            while True:
                try:
                    # Wait for updates with timeout
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(update)}\n\n"

                    # Break if task is completed
                    if update.get('status') in ['completed', 'error']:
                        break

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

        except Exception as e:
            logger.error(f"SSE stream error: {e}")
        finally:
            # Remove subscriber
            if task_id in progress_subscribers:
                try:
                    progress_subscribers[task_id].remove(queue)
                    if not progress_subscribers[task_id]:
                        del progress_subscribers[task_id]
                except ValueError:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

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
    background_tasks.add_task(import_readwise_background, task_id, request.folder_path)
    
    return {"task_id": task_id, "message": "Readwise import started"}

async def import_readwise_background(task_id: str, folder_path: str):
    """Background task for importing Readwise data."""
    try:
        # Update progress callback
        async def progress_callback(progress: float, message: str):
            if task_id in processing_tasks:
                processing_tasks[task_id].progress = progress
                processing_tasks[task_id].message = message

                # Notify SSE subscribers
                await notify_progress_subscribers(task_id, processing_tasks[task_id].dict())
        
        # Import highlights from folder
        from pathlib import Path

        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        await progress_callback(10.0, "Scanning for markdown files...")

        # Find markdown files
        markdown_files = list(folder.glob("*.md")) + list(folder.glob("*.markdown"))

        if not markdown_files:
            raise ValueError("No markdown files found in the specified folder")

        await progress_callback(20.0, f"Found {len(markdown_files)} markdown files")

        total_highlights = 0
        processed_files = 0

        for i, file_path in enumerate(markdown_files):
            try:
                await progress_callback(20.0 + (i / len(markdown_files)) * 60.0, f"Processing {file_path.name}...")

                # Import highlights from this file
                highlights = await backend.readwise_importer.import_from_file(str(file_path))

                if highlights:
                    # Store highlights in vector database
                    for highlight in highlights:
                        # Create a document-like structure for the highlight
                        highlight_doc = {
                            'content': highlight['text'],
                            'metadata': {
                                'source': f"readwise_{highlight['book']}",
                                'book': highlight['book'],
                                'author': highlight['author'],
                                'highlight_id': highlight['id'],
                                'tags': highlight.get('tags', []),
                                'location': highlight.get('location', ''),
                                'note': highlight.get('note', ''),
                                'source_type': 'readwise'
                            }
                        }

                        # Add to vector store
                        await backend.vector_store.add_single_document(
                            content=highlight_doc['content'],
                            metadata=highlight_doc['metadata']
                        )

                    total_highlights += len(highlights)
                    processed_files += 1

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        results = {
            "highlights_imported": total_highlights,
            "files_processed": processed_files,
            "total_files": len(markdown_files)
        }
        
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
        # Clear all documents from the vector store
        if backend.vector_store and backend.vector_store.table:
            # Delete all rows from the table
            backend.vector_store.table.delete("id IS NOT NULL")
            logger.info("All documents cleared from database")
            return {"message": "All documents cleared successfully", "cleared_count": "all"}
        else:
            return {"message": "No database table found"}
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/folders/scan")
async def scan_folder(request: FolderScanRequest):
    """Scan a folder for supported files."""
    try:
        import os
        from pathlib import Path

        folder_path = Path(request.folder_path)
        if not folder_path.exists():
            raise HTTPException(status_code=404, detail="Folder not found")

        supported_extensions = {'.txt', '.md', '.pdf', '.docx'}
        files = []

        # Get folder manager for indexing status if available
        folder_manager = None
        if backend and hasattr(backend, 'folder_manager'):
            folder_manager = backend.folder_manager

        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                stat = file_path.stat()
                file_info = {
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": file_path.suffix.lower(),
                    "type": "file",
                    "relative_path": str(file_path.relative_to(folder_path))
                }

                # Add indexing status if folder manager is available
                if folder_manager:
                    indexing_status = folder_manager.get_indexing_status(str(file_path))
                    file_info.update({
                        "indexing_status": indexing_status.get('status', 'unknown'),
                        "indexing_progress": indexing_status.get('progress', 0.0),
                        "indexing_error": indexing_status.get('error'),
                        "needs_processing": folder_manager.file_needs_processing(str(file_path), stat.st_mtime)
                    })
                else:
                    file_info.update({
                        "indexing_status": "unknown",
                        "indexing_progress": 0.0,
                        "indexing_error": None,
                        "needs_processing": True
                    })

                files.append(file_info)

        return {"files": files, "folder_path": str(folder_path)}

    except Exception as e:
        logger.error(f"Folder scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/folders/list")
async def list_connected_folders():
    """List connected folders."""
    # Return only test_docs as the primary folder
    return {
        "connected_folders": [
            "test_docs"
        ]
    }

@app.post("/folders/add")
async def add_folder(request: FolderAddRequest):
    """Add a folder to monitoring."""
    # For now, just return success
    return {"message": f"Folder {request.folder_path} added successfully"}

@app.get("/indexing/status")
async def get_indexing_status(file_path: Optional[str] = None):
    """Get indexing status for files."""
    if not backend or not hasattr(backend, 'folder_manager'):
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        folder_manager = backend.folder_manager
        if file_path:
            status = folder_manager.get_indexing_status(file_path)
            return {"file_path": file_path, "status": status}
        else:
            all_status = folder_manager.get_indexing_status()
            return {"indexing_status": all_status}
    except Exception as e:
        logger.error(f"Error getting indexing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/indexing/trigger")
async def trigger_indexing(request: TriggerIndexingRequest):
    """Trigger indexing for specific files."""
    if not backend or not hasattr(backend, 'folder_manager'):
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        folder_manager = backend.folder_manager

        # Queue files for processing
        for file_path in request.file_paths:
            folder_manager.queue_file_for_processing(file_path, 'manual_trigger')

        return {
            "message": f"Triggered indexing for {len(request.file_paths)} files",
            "file_paths": request.file_paths
        }
    except Exception as e:
        logger.error(f"Error triggering indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/indexing/process-direct")
async def process_files_directly(request: TriggerIndexingRequest):
    """Directly process files using the backend (for testing)."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        # Process files directly using the backend
        results = await backend.process_documents(request.file_paths)

        return {
            "message": f"Processed {len(request.file_paths)} files directly",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error processing files directly: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/indexing/status/stream")
async def stream_indexing_status():
    """Stream real-time indexing status updates via Server-Sent Events."""
    if not backend or not hasattr(backend, 'folder_manager'):
        raise HTTPException(status_code=500, detail="Backend not initialized")

    async def event_stream():
        # Create a queue for this subscriber
        queue = asyncio.Queue()
        folder_manager = backend.folder_manager

        # Add to subscribers
        folder_manager.add_status_subscriber(queue)

        try:
            # Send initial status
            initial_status = folder_manager.get_indexing_status()
            yield f"data: {json.dumps({'type': 'initial', 'data': initial_status})}\n\n"

            # Stream updates
            while True:
                try:
                    # Wait for updates with timeout
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(update)}\n\n"

                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            # Remove subscriber
            folder_manager.remove_status_subscriber(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

# Readwise Integration Endpoints





# Settings Management Endpoints
class SettingsRequest(BaseModel):
    theme: Optional[str] = "system"
    chunkSize: Optional[int] = 1000
    chunkOverlap: Optional[int] = 200
    autoIndex: Optional[bool] = True
    alwaysOnTop: Optional[bool] = False
    autoHide: Optional[bool] = True
    showNotifications: Optional[bool] = True
    showErrors: Optional[bool] = True

@app.get("/settings")
async def get_settings():
    """Get current application settings."""
    try:
        # Load settings from config
        settings_file = Path("settings.json")
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            # Default settings
            settings = {
                "theme": "system",
                "chunkSize": 1000,
                "chunkOverlap": 200,
                "autoIndex": True,
                "alwaysOnTop": False,
                "autoHide": True,
                "showNotifications": True,
                "showErrors": True
            }

        return settings

    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/settings")
async def update_settings(request: SettingsRequest):
    """Update application settings."""
    try:
        # Convert to dict
        settings = request.dict()

        # Save to file
        settings_file = Path("settings.json")
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        # Update backend config if needed
        if backend and hasattr(backend, 'config'):
            backend.config.chunk_size = settings.get('chunkSize', 1000)
            backend.config.chunk_overlap = settings.get('chunkOverlap', 200)

        return {"status": "success", "message": "Settings updated successfully"}

    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document Management Endpoints
@app.get("/documents")
async def get_documents(limit: int = 50, offset: int = 0):
    """Get list of indexed documents."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        # Get documents from vector store
        documents = await backend.vector_store.get_documents(limit=limit, offset=offset)
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        # Delete from vector store
        await backend.vector_store.delete_document(document_id)
        return {"status": "success", "message": f"Document {document_id} deleted"}

    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/database/clear")
async def clear_database():
    """Clear all data from the database."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        # Clear vector store
        await backend.vector_store.clear()
        return {"status": "success", "message": "Database cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/suggestions")
async def get_suggestions(q: str = ""):
    """Get search suggestions based on partial query."""
    if not backend:
        raise HTTPException(status_code=500, detail="Backend not initialized")

    try:
        # Get suggestions from search engine
        suggestions = await backend.search_engine.get_suggestions(q)
        return {"suggestions": suggestions}

    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process/status/{task_id}")
async def get_processing_status(task_id: str):
    """Get the status of a processing task."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return processing_tasks[task_id].dict()

# ============================================================================
# NEW ENHANCED API ENDPOINTS
# ============================================================================

# Citation Management Endpoints
class CitationRequest(BaseModel):
    content: str
    source_id: str
    page: Optional[str] = ""
    location: Optional[str] = ""
    highlight_color: Optional[str] = ""
    user_note: Optional[str] = ""
    tags: Optional[List[str]] = []
    importance: Optional[str] = "medium"

class SourceRequest(BaseModel):
    title: str
    author: Optional[str] = ""
    authors: Optional[List[str]] = []
    publication_date: Optional[str] = ""
    publisher: Optional[str] = ""
    url: Optional[str] = ""
    doi: Optional[str] = ""
    isbn: Optional[str] = ""
    file_path: Optional[str] = ""
    tags: Optional[List[str]] = []
    notes: Optional[str] = ""

@app.post("/citations/sources")
async def register_source(source: SourceRequest):
    """Register a new source for citations."""
    try:
        if not backend or not hasattr(backend, 'citation_manager'):
            raise HTTPException(status_code=503, detail="Citation manager not available")

        source_id = backend.citation_manager.register_source(source.dict())
        return {"source_id": source_id, "message": "Source registered successfully"}
    except Exception as e:
        logger.error(f"Error registering source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/citations")
async def create_citation(citation: CitationRequest):
    """Create a new citation."""
    try:
        if not backend or not hasattr(backend, 'citation_manager'):
            raise HTTPException(status_code=503, detail="Citation manager not available")

        citation_obj = backend.citation_manager.create_citation(**citation.dict())
        return {"citation": citation_obj, "message": "Citation created successfully"}
    except Exception as e:
        logger.error(f"Error creating citation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/citations/{citation_id}/format")
async def format_citation(citation_id: str, style: Optional[str] = "apa"):
    """Format a citation in the specified style."""
    try:
        if not backend or not hasattr(backend, 'citation_manager'):
            raise HTTPException(status_code=503, detail="Citation manager not available")

        formatted = backend.citation_manager.format_citation(citation_id, style)
        return {"formatted_citation": formatted}
    except Exception as e:
        logger.error(f"Error formatting citation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/citations/statistics")
async def get_citation_statistics():
    """Get citation database statistics."""
    try:
        if not backend or not hasattr(backend, 'citation_manager'):
            raise HTTPException(status_code=503, detail="Citation manager not available")

        stats = backend.citation_manager.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting citation statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background Processing Endpoints
@app.get("/tasks")
async def get_tasks():
    """Get all background tasks."""
    try:
        if not backend or not hasattr(backend, 'background_processor'):
            raise HTTPException(status_code=503, detail="Background processor not available")

        summary = backend.background_processor.get_task_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task by ID."""
    try:
        if not backend or not hasattr(backend, 'background_processor'):
            raise HTTPException(status_code=503, detail="Background processor not available")

        task = backend.background_processor.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"task": task.__dict__}
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a background task."""
    try:
        if not backend or not hasattr(backend, 'background_processor'):
            raise HTTPException(status_code=503, detail="Background processor not available")

        success = await backend.background_processor.cancel_task(task_id)
        if success:
            return {"message": "Task cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Task could not be cancelled")
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/statistics")
async def get_processing_statistics():
    """Get background processing statistics."""
    try:
        if not backend or not hasattr(backend, 'background_processor'):
            raise HTTPException(status_code=503, detail="Background processor not available")

        stats = backend.background_processor.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting processing statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User Annotation Endpoints
class UserAnnotationRequest(BaseModel):
    file_path: str
    page_num: int
    annotation_data: Dict[str, Any]

@app.post("/annotations")
async def add_user_annotation(annotation: UserAnnotationRequest):
    """Add a user annotation to a document."""
    try:
        if not backend or not hasattr(backend, 'document_processor'):
            raise HTTPException(status_code=503, detail="Document processor not available")

        success = await backend.document_processor.add_user_annotation(
            annotation.file_path,
            annotation.page_num,
            annotation.annotation_data
        )

        if success:
            return {"message": "Annotation added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add annotation")
    except Exception as e:
        logger.error(f"Error adding annotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/annotations/{file_path:path}")
async def get_user_annotations(file_path: str):
    """Get all user annotations for a document."""
    try:
        if not backend or not hasattr(backend, 'document_processor'):
            raise HTTPException(status_code=503, detail="Document processor not available")

        annotations = await backend.document_processor.get_user_annotations(file_path)
        return {"annotations": annotations}
    except Exception as e:
        logger.error(f"Error getting annotations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document Monitoring Endpoints
@app.post("/monitoring/start")
async def start_document_monitoring():
    """Start document monitoring."""
    try:
        if not backend or not hasattr(backend, 'document_monitor'):
            raise HTTPException(status_code=503, detail="Document monitor not available")

        await backend.document_monitor.start_monitoring()
        return {"message": "Document monitoring started"}
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/stop")
async def stop_document_monitoring():
    """Stop document monitoring."""
    try:
        if not backend or not hasattr(backend, 'document_monitor'):
            raise HTTPException(status_code=503, detail="Document monitor not available")

        await backend.document_monitor.stop_monitoring()
        return {"message": "Document monitoring stopped"}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
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
