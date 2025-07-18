"""
Background Processing System for Semantic Search Assistant.
Handles non-blocking document processing with real-time progress updates.
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class ProcessingTask:
    id: str
    name: str
    description: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    progress: float = 0.0
    total_steps: int = 1
    current_step: int = 0
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    error_message: str = ""
    result: Any = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

class BackgroundProcessor:
    """Manages background processing tasks with progress tracking."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_workers = config.get('processing.max_workers', 4)
        self.max_queue_size = config.get('processing.max_queue_size', 100)
        
        # Task management
        self.tasks: Dict[str, ProcessingTask] = {}
        self.task_queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Progress callbacks
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        
        # Processing state
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
    
    async def start(self):
        """Start the background processor."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"🚀 Starting background processor with {self.max_workers} workers")
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
        
        logger.info("✅ Background processor started")
    
    async def stop(self):
        """Stop the background processor."""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping background processor...")
        self.is_running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("✅ Background processor stopped")
    
    async def submit_task(self, task_func: Callable, task_name: str, 
                         task_description: str = "", task_type: str = "general",
                         priority: TaskPriority = TaskPriority.NORMAL,
                         **kwargs) -> str:
        """Submit a task for background processing."""
        task_id = str(uuid.uuid4())
        
        task = ProcessingTask(
            id=task_id,
            name=task_name,
            description=task_description,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            metadata=kwargs
        )
        
        self.tasks[task_id] = task
        self.stats['total_tasks'] += 1
        
        # Add to queue with priority
        await self.task_queue.put((priority.value, task_id, task_func, kwargs))
        
        logger.info(f"📝 Submitted task: {task_name} (ID: {task_id})")
        await self._notify_progress_callbacks(task)
        
        return task_id
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes tasks from the queue."""
        logger.info(f"👷 Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                try:
                    priority, task_id, task_func, kwargs = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                task = self.tasks.get(task_id)
                if not task:
                    continue
                
                logger.info(f"🔄 Worker {worker_name} processing task: {task.name}")
                
                # Update task status
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now().isoformat()
                await self._notify_progress_callbacks(task)
                
                # Execute task
                start_time = time.time()
                try:
                    # Create progress callback for this task
                    progress_callback = lambda progress, step=None, total=None: asyncio.create_task(
                        self._update_task_progress(task_id, progress, step, total)
                    )
                    
                    # Run task in executor
                    if asyncio.iscoroutinefunction(task_func):
                        result = await task_func(progress_callback=progress_callback, **kwargs)
                    else:
                        result = await asyncio.get_event_loop().run_in_executor(
                            self.executor, 
                            lambda: task_func(progress_callback=progress_callback, **kwargs)
                        )
                    
                    # Task completed successfully
                    processing_time = time.time() - start_time
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now().isoformat()
                    task.progress = 100.0
                    task.result = result
                    
                    self.stats['completed_tasks'] += 1
                    self.stats['total_processing_time'] += processing_time
                    self.stats['average_processing_time'] = (
                        self.stats['total_processing_time'] / self.stats['completed_tasks']
                    )
                    
                    logger.info(f"✅ Task completed: {task.name} ({processing_time:.2f}s)")
                    
                except Exception as e:
                    # Task failed
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now().isoformat()
                    task.error_message = str(e)
                    
                    self.stats['failed_tasks'] += 1
                    
                    logger.error(f"❌ Task failed: {task.name} - {e}")
                
                # Notify callbacks
                await self._notify_progress_callbacks(task)
                await self._notify_completion_callbacks(task)
                
                # Mark queue task as done
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"👷 Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Worker {worker_name} error: {e}")
        
        logger.info(f"👷 Worker {worker_name} stopped")
    
    async def _update_task_progress(self, task_id: str, progress: float, 
                                  current_step: Optional[int] = None,
                                  total_steps: Optional[int] = None):
        """Update task progress."""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.progress = min(100.0, max(0.0, progress))
        
        if current_step is not None:
            task.current_step = current_step
        
        if total_steps is not None:
            task.total_steps = total_steps
        
        await self._notify_progress_callbacks(task)
    
    async def _notify_progress_callbacks(self, task: ProcessingTask):
        """Notify all progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    async def _notify_completion_callbacks(self, task: ProcessingTask):
        """Notify all completion callbacks."""
        for callback in self.completion_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task)
                else:
                    callback(task)
            except Exception as e:
                logger.error(f"Error in completion callback: {e}")
    
    def add_progress_callback(self, callback: Callable):
        """Add a progress callback."""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable):
        """Add a completion callback."""
        self.completion_callbacks.append(callback)
    
    def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[ProcessingTask]:
        """Get all tasks with the specified status."""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_type(self, task_type: str) -> List[ProcessingTask]:
        """Get all tasks of the specified type."""
        return [task for task in self.tasks.values() if task.task_type == task_type]
    
    def get_active_tasks(self) -> List[ProcessingTask]:
        """Get all active (running or pending) tasks."""
        return [
            task for task in self.tasks.values() 
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        ]
    
    def get_recent_tasks(self, limit: int = 10) -> List[ProcessingTask]:
        """Get the most recent tasks."""
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        return sorted_tasks[:limit]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now().isoformat()
            self.stats['cancelled_tasks'] += 1
            
            await self._notify_progress_callbacks(task)
            await self._notify_completion_callbacks(task)
            
            logger.info(f"🚫 Task cancelled: {task.name}")
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        active_tasks = len(self.get_active_tasks())
        queue_size = self.task_queue.qsize()
        
        return {
            **self.stats,
            'active_tasks': active_tasks,
            'queue_size': queue_size,
            'worker_count': self.max_workers,
            'is_running': self.is_running
        }
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get a summary of all tasks."""
        status_counts = {}
        type_counts = {}
        
        for task in self.tasks.values():
            # Count by status
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            task_type = task.task_type
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        return {
            'total_tasks': len(self.tasks),
            'status_counts': status_counts,
            'type_counts': type_counts,
            'recent_tasks': [asdict(task) for task in self.get_recent_tasks(5)]
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                try:
                    task_time = datetime.fromisoformat(task.completed_at).timestamp()
                    if task_time < cutoff_time:
                        tasks_to_remove.append(task_id)
                except:
                    # If we can't parse the time, remove it anyway
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"🧹 Cleaned up {len(tasks_to_remove)} old tasks")
    
    def export_task_history(self, file_path: str):
        """Export task history to a JSON file."""
        try:
            history = {
                'exported_at': datetime.now().isoformat(),
                'statistics': self.get_statistics(),
                'tasks': [asdict(task) for task in self.tasks.values()]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Task history exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting task history: {e}")

# Utility functions for common background tasks

async def process_document_task(file_path: str, document_processor, progress_callback=None, **kwargs):
    """Background task for processing a single document."""
    try:
        if progress_callback:
            progress_callback(10.0, 1, 5)
        
        # Process the document
        result = await document_processor.process_file(file_path)
        
        if progress_callback:
            progress_callback(100.0, 5, 5)
        
        return result
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {e}")
        raise

async def batch_process_documents_task(file_paths: List[str], document_processor, 
                                     progress_callback=None, **kwargs):
    """Background task for processing multiple documents."""
    results = []
    total_files = len(file_paths)
    
    for i, file_path in enumerate(file_paths):
        try:
            if progress_callback:
                progress = (i / total_files) * 100
                progress_callback(progress, i + 1, total_files)
            
            result = await document_processor.process_file(file_path)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            results.append({'error': str(e), 'file_path': file_path})
    
    if progress_callback:
        progress_callback(100.0, total_files, total_files)
    
    return results

async def index_folder_task(folder_path: str, document_processor, search_engine,
                          progress_callback=None, **kwargs):
    """Background task for indexing an entire folder."""
    folder = Path(folder_path)
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")
    
    # Find all supported files
    supported_extensions = ['.pdf', '.docx', '.md', '.txt']
    files = []
    for ext in supported_extensions:
        files.extend(folder.rglob(f'*{ext}'))
    
    if not files:
        return {'message': 'No supported files found', 'processed_count': 0}
    
    total_files = len(files)
    processed_count = 0
    
    for i, file_path in enumerate(files):
        try:
            if progress_callback:
                progress = (i / total_files) * 100
                progress_callback(progress, i + 1, total_files)
            
            # Process and index the file
            chunks = await document_processor.process_file(str(file_path))
            if chunks:
                await search_engine.add_documents(chunks)
                processed_count += 1
            
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
    
    if progress_callback:
        progress_callback(100.0, total_files, total_files)
    
    return {
        'message': f'Indexed {processed_count} of {total_files} files',
        'processed_count': processed_count,
        'total_files': total_files
    }
